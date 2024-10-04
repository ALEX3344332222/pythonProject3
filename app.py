from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Cookie, Request, Response
from sqlalchemy.orm import Session
from database import SessionLocal, AudioTrack, create_or_update_user, User, Playlist, PlaylistTrack
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.staticfiles import StaticFiles
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1
import shutil
import uvicorn
import httpx
from starlette.middleware.sessions import SessionMiddleware
import base64


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/mp3_files", StaticFiles(directory="mp3_files"), name="mp3_files")
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/styles", StaticFiles(directory="styles"), name="styles")

app.add_middleware(SessionMiddleware, secret_key="your-very-secret-key")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Яндекс OAuth конфигурация
YANDEX_CLIENT_ID = '983a1fbebb3b4b6a851c645b7bb541bf'
YANDEX_CLIENT_SECRET = '690a8031ac6546d48d49542d82cff3eb'
YANDEX_REDIRECT_URI = 'http://localhost:8000/oauth.php?provider=yandex'
YANDEX_AUTH_URL = 'https://oauth.yandex.ru/authorize'
YANDEX_TOKEN_URL = 'https://oauth.yandex.ru/token'


@app.get("/", response_class=HTMLResponse)
async def music_library(request: Request, db: Session = Depends(get_db)):
    tracks = db.query(AudioTrack).all()
    return templates.TemplateResponse("index.html", {"request": request, "tracks": tracks, "session": request.session})

@app.get("/mp3/{track_id}")
def download_mp3(track_id: int, db: Session = Depends(get_db)):
    track = db.query(AudioTrack).filter(AudioTrack.track_id == track_id).first()

    if not track:
        raise HTTPException(status_code=404, detail="MP3 file not found")

    file_path = track.file_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="audio/mpeg", filename=track.title)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Сохраняем файл на диск
    file_location = f"mp3_files/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Извлекаем метаданные из файла MP3
    audio = MP3(file_location, ID3=ID3)

    title = audio.get('TIT2', 'Unknown Title').text[0] if audio.get('TIT2') else 'Unknown Title'
    artist = audio.get('TPE1', 'Unknown Artist').text[0] if audio.get('TPE1') else 'Unknown Artist'

    # Извлекаем изображение из метаданных
    image_data = None
    if 'APIC:' in audio:
        image_data = audio['APIC:'].data

    # Сохраняем изображение на диск, если оно существует
    image_path = None
    if image_data:
        image_path = f"images/{file.filename}.jpg"
        with open(image_path, "wb") as img_file:
            img_file.write(image_data)

    # Создаем новую запись в базе данных
    new_track = AudioTrack(
        title=title,
        artist=artist,
        file_path=f"/mp3_files/{file.filename}",
        file_path_img=f"/images/{file.filename}.jpg" if image_path else None
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)

    return {"status": "success", "message": "File uploaded successfully"}
@app.get("/auth/login")
async def login():
    auth_url = (
        f"{YANDEX_AUTH_URL}?response_type=code&client_id={YANDEX_CLIENT_ID}&redirect_uri={YANDEX_REDIRECT_URI}"
    )
    return RedirectResponse(url=auth_url)


@app.get("/oauth.php")
async def oauth_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Code not found in request")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            YANDEX_TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': YANDEX_REDIRECT_URI,
                'client_id': YANDEX_CLIENT_ID,
                'client_secret': YANDEX_CLIENT_SECRET,
                'device_id': '983a1fbebb3b4b6a851c645b7bb541bf',
            },
        )

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')

            request.session['access_token'] = access_token

            user_info_response = await client.get(
                'https://login.yandex.ru/info',
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if user_info_response.status_code == 200:
                user_info = user_info_response.json()

                print(user_info)
                # Сохранение или обновление пользователя в базе данных
                create_or_update_user(db, user_info)
                # Устанавливаем user_id в сессии
                request.session['user_id'] = user_info['id']
                request.session['avatar_url'] = user_info['default_avatar_id']
                request.session['real_name'] = user_info['real_name']
                print(request.session)
                # Вернуть сообщение об успешном сохранении данных и перенаправление на главную страницу
                return RedirectResponse(url="/")
            else:
                raise HTTPException(status_code=400, detail="Failed to obtain user info")

        else:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")


@app.get("/auth/logout")
async def logout(request: Request):
    # Получаем токен из сессии
    access_token = request.session.get('access_token')

    # Печатаем токен для отладки
    print(f"Access Token: {access_token}")

    # Кодирование client_id и client_secret в Base64
    basic_auth_str = f"{YANDEX_CLIENT_ID}:{YANDEX_CLIENT_SECRET}"
    basic_auth_bytes = base64.b64encode(basic_auth_str.encode('utf-8')).decode('utf-8')

    # Если токен найден, отзываем его
    if access_token:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://oauth.yandex.ru/revoke_token',
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {basic_auth_bytes}',
                },
                data={
                    'access_token': access_token,
                    # Если известно, добавляем device_id
                    'device_id': YANDEX_CLIENT_ID,
                }
            )

            if response.status_code == 200:
                print('Токен успешно отозван')
            else:
                print('Ошибка при отзыве токена:', response.json())

    # Создаем редирект на главную страницу
    response = RedirectResponse(url="/")

    # Удаляем куки
    response.delete_cookie('session')

    # Очистка информации о пользователе в сессии
    request.session.clear()

    return response


@app.post("/add-to-playlist")
async def add_to_playlist(request: Request, db: Session = Depends(get_db), track_id: int = Form(...)):
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated, bro 😬")

    # Проверяем, есть ли плейлист "My_music" для текущего пользователя
    playlist = db.query(Playlist).filter(Playlist.name == "My_music").first()

    if not playlist:
        playlist = Playlist(name="My_music")
        db.add(playlist)
        db.commit()
        db.refresh(playlist)

    # Проверяем, добавлен ли этот трек уже для данного пользователя
    existing_entry = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == playlist.playlist_id,
        PlaylistTrack.track_id == track_id,
        PlaylistTrack.user_id == user_id
    ).first()

    if existing_entry:
        return {"message": "Трек уже в плейлисте 'My_music'", "already_exists": True}

    playlist_track = PlaylistTrack(
        playlist_id=playlist.playlist_id,
        track_id=track_id,
        user_id=user_id
    )
    db.add(playlist_track)
    db.commit()

    return {"message": "Трек добавлен в плейлист 'My_music'", "already_exists": False}

@app.get("/my-music", response_class=HTMLResponse)
async def my_music(request: Request, db: Session = Depends(get_db)):
    # Получаем user_id из сессии
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Получаем плейлист "My_music" для текущего пользователя
    playlist = db.query(Playlist).filter(Playlist.name == "My_music").first()

    if playlist:
        # Извлекаем треки, которые были добавлены пользователем в плейлист
        tracks = db.query(AudioTrack).join(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist.playlist_id,
            PlaylistTrack.user_id == user_id
        ).all()
    else:
        tracks = []  # Если плейлист не найден, возвращаем пустой список

    # Возвращаем HTML-ответ с треками
    return templates.TemplateResponse("my_music.html", {"request": request, "tracks": tracks})


@app.post("/remove-from-playlist")
async def remove_from_playlist(request: Request, db: Session = Depends(get_db), track_id: int = Form(...)):
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated, bro 😬")

    # Проверяем, есть ли плейлист "My_music" для текущего пользователя
    playlist = db.query(Playlist).filter(Playlist.name == "My_music").first()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist 'My_music' not found")

    # Находим запись о треке в плейлисте
    playlist_track = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == playlist.playlist_id,
        PlaylistTrack.track_id == track_id,
        PlaylistTrack.user_id == user_id
    ).first()

    if not playlist_track:
        return {"message": "Трек не найден в плейлисте 'My_music'", "not_found": True}

    # Удаляем запись о треке из плейлиста
    db.delete(playlist_track)
    db.commit()

    return {"message": "Трек удален из плейлиста 'My_music'", "not_found": False}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)