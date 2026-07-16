import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Telegram
TOKEN = os.getenv("TOKEN", "8854497322:AAE1IsRJRInUo2EDpWkZNxOoby3B--4cWq0")

# Configuración del servidor
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configuración de archivos
MAX_FILE_SIZE = 2.5 * 1024 * 1024 * 1024  # 2.5 GB
FILE_EXPIRATION_HOURS = 24
CLEANUP_INTERVAL = 3600  # 1 hora

# Formatos soportados
VIDEO_FORMATS = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
AUDIO_FORMATS = ('.mp3', '.wav', '.m4a', '.aac', '.flac')
