# import os

# class Config:
#     SQLALCHEMY_DATABASE_URI = "YOUR_SUPABASE_CONNECTION_STRING"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SECRET_KEY = "your_secret_key"


# class Config:
#     SQLALCHEMY_DATABASE_URI = "sqlite:///diary.db"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SECRET_KEY = "your_secret_key"

import os
from dotenv  import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "mansi_secret"