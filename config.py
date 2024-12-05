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

MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_FROM = os.environ.get('MAIL_FROM')
MAIL_PORT = os.environ.get('MAIL_PORT')
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')



BASE_DIR=Path(__file__).resolve().parent.parent
PHOTO_DIR = Path(BASE_DIR) /'placebook'/ 'media' / 'photos'
PHOTO_DIR.mkdir(parents=True, exist_ok=True)



