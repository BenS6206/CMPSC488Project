# my_project/config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret")
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:password@localhost:5432/my_postgis_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False