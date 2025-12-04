import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv()

# Ollama model configuration (runs locally, no API key needed)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

_DEFAULT_DB_PATH = DATA_DIR / "journals.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")