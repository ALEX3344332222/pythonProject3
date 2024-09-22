from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

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

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Playlist(Base):
    __tablename__ = "playlists"

    playlist_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    name = Column(String, nullable=False)
    user = relationship("User")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_tracks_id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey('playlists.playlist_id'), nullable=False)
    track_id = Column(Integer, ForeignKey('audio_tracks.track_id'), nullable=False)
    added_at = Column(TIMESTAMP, default=datetime.utcnow)
    playlist = relationship("Playlist")
    track = relationship("AudioTrack")

Base.metadata.create_all(bind=engine)
