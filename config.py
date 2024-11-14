import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
SECRET = os.environ.get('SECRET')

BASE_DIR=Path(__file__).resolve().parent.parent
PHOTO_DIR = Path(BASE_DIR) /'fastApiProject'/ 'media' / 'photos'
PHOTO_DIR.mkdir(parents=True, exist_ok=True)