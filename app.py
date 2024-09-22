from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import SessionLocal, AudioTrack
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.staticfiles import StaticFiles
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1
import shutil
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/mp3_files", StaticFiles(directory="mp3_files"), name="mp3_files")
app.mount("/images", StaticFiles(directory="images"), name="images")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def music_library(request: Request, db: Session = Depends(get_db)):
    tracks = db.query(AudioTrack).all()
    return templates.TemplateResponse("index.html", {"request": request, "tracks": tracks})

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)