# my_project/config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret")
<<<<<<< HEAD
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:password@localhost:5432/my_postgis_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
=======
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:Census1234@34.58.78.90:5432/census-data"

>>>>>>> 00d854b6 (Reinitialized Git inside the correct project folder)
