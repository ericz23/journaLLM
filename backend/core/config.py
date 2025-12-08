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

# WHOOP OAuth Configuration
WHOOP_CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID", "")
WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")
WHOOP_REDIRECT_URI = os.environ.get("WHOOP_REDIRECT_URI", "http://localhost:8000/api/whoop/callback")

# WHOOP OAuth URLs
WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_API_BASE_URL = "https://api.prod.whoop.com/developer"

# Scopes to request (add 'offline' to get refresh tokens)
# Available scopes: read:profile, read:recovery, read:cycles, read:sleep, read:workout, read:body_measurement
WHOOP_SCOPES = os.environ.get(
    "WHOOP_SCOPES",
    "offline read:profile read:recovery read:cycles read:sleep read:workout read:body_measurement"
)