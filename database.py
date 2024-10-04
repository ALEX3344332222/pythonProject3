from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
from fastapi import Depends
from pydantic import BaseModel

DATABASE_URL = "postgresql://postgres:123@pythonproject3-db-1:5432/volume"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AudioTrack(Base):
    __tablename__ = "audio_tracks"

    track_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    file_path_img = Column(String, nullable=True)

    playlists = relationship("PlaylistTrack", back_populates="track")


class User(Base):
    __tablename__ = "users"

    # Основные поля
    yandex_id = Column(String, primary_key=True, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=True)  # Используем как login
    email = Column(String, unique=True, nullable=True)  # Может быть пустым, если не предоставляется
    password_hash = Column(String, nullable=True)  # Необязательно, так как авторизация через Яндекс

    # Дополнительные поля от Яндекс
    display_name = Column(String, nullable=True)
    real_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    psuid = Column(String, nullable=True)

    playlists = relationship("PlaylistTrack", back_populates="user")

class Playlist(Base):
    __tablename__ = "playlists"

    playlist_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    tracks = relationship("PlaylistTrack", back_populates="playlist")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_tracks_id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey('playlists.playlist_id'), nullable=False)
    track_id = Column(Integer, ForeignKey('audio_tracks.track_id'), nullable=False)
    user_id = Column(String, ForeignKey('users.yandex_id'), nullable=False)
    added_at = Column(TIMESTAMP, default=datetime.utcnow)

    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("AudioTrack", back_populates="playlists")
    user = relationship("User", back_populates="playlists")


def create_or_update_user(db: Session, user_info: dict):
    # Проверка, существует ли пользователь с данным Yandex ID
    avatar_id = user_info.get('default_avatar_id')
    avatar_url = f"https://avatars.mds.yandex.net/get-yapic/{avatar_id}/islands-200" if avatar_id else None

    db_user = db.query(User).filter(User.yandex_id == user_info['id']).first()
    if db_user:
        # Если пользователь существует, обновляем его данные
        db_user.username = user_info['login']
        db_user.display_name = user_info['display_name']
        db_user.real_name = user_info['real_name']
        db_user.first_name = user_info['first_name']
        db_user.last_name = user_info['last_name']
        db_user.phone_number = user_info['default_phone']['number'] if user_info.get('default_phone') else None
        db_user.avatar_url = avatar_url
        db_user.psuid = user_info['psuid']
    else:
        # Если пользователя нет, создаем нового
        new_user = User(
            yandex_id=user_info['id'],
            username=user_info['login'],
            display_name=user_info['display_name'],
            real_name=user_info['real_name'],
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            phone_number=user_info['default_phone']['number'] if user_info.get('default_phone') else None,
            avatar_url=avatar_url,
            psuid=user_info['psuid']
        )
        db.add(new_user)
    db.commit()




Base.metadata.create_all(bind=engine)
