from dotenv import load_dotenv
import os

load_dotenv()
BASE = os.path.curdir

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{BASE}/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    CREATIVE_MODEL = os.getenv("CREATIVE_MODEL", "qwen3.5:397b-cloud")
    CRITIC_MODEL = os.getenv("CRITIC_MODEL", "gemma4:31b-cloud")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
