import os
import subprocess

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pytubefix import YouTube
from dotenv import load_dotenv

YT_BASE_URL = "https://www.youtube.com/watch?v="

Base = declarative_base()

class Song(Base):
    __tablename__ = 'song'
    youtubeid = Column(String(100), primary_key=True)
    name = Column(String(100))
    artist = Column(String(100))
    downloaded = Column(Integer)

def get_session():
    
    try:
        mariadb_pass = os.environ.get("MYSQL_ROOT_PASSWORD")
        mariadb_host = os.environ.get("MYSQL_HOST")
        engine_string = 'mysql+pymysql://root:' + str(mariadb_pass) + "@" + str(mariadb_host) + '/managerzone'
        engine = create_engine(engine_string)
    except Exception as e:
        return None
    
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    return session

load_dotenv()

session = get_session()

songs = session.query(Song).filter_by(downloaded=0)

count = 0
for song in songs:
    filename = os.environ.get("LOCAL_PATH") + str(song.youtubeid) + ".mp4"
    download_url = YT_BASE_URL + str(song.youtubeid)
    try:
        YouTube(download_url).streams.first().download(filename=filename)
    except Exception as e:
        continue
    count += 1
    
if count > 0:
    rsync_cmd = ["rsync", "-avz"]
    rsync_cmd.extend([os.environ.get("LOCAL_PATH"), os.environ.get("REMOTE_PATH")])
    try:
        result = subprocess.run(rsync_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"rsync failed with error: {e}")
    else:
        print(result.stdout)

