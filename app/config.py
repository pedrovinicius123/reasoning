from dotenv import load_dotenv
import os

load_dotenv()
BASE = os.path.curdir

class Config:
    SECRET_KEY=os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{BASE}/app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS=False
