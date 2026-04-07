from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from ollama import Client
from dotenv import load_dotenv
import os
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
m = Marshmallow()

load_dotenv()

# Configure Ollama client.
# The ollama client already reads OLLAMA_API_KEY from the environment,
# so we only need to pass the host explicitly.
client = Client(host=Config.OLLAMA_HOST)
