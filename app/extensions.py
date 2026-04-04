from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from ollama import Client
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()
m = Marshmallow()

load_dotenv()

client = Client(
    "https://ollama.com/api",
    headers={
        "authorization": f"Bearer {os.getenv("OLLAMA_API_KEY")}"
    }
)
