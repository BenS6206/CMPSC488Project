# my_project/models.py
from .database import db
from geoalchemy2 import Geometry

class MyArea(db.Model):
    __tablename__ = "my_area"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    population = db.Column(db.Integer)
    geom = db.Column(Geometry("POLYGON", srid=4326))  # Geospatial field

class CensusData(db.Model):
    __tablename__ = "census_data"

    id = db.Column(db.Integer, primary_key=True)
    county = db.Column(db.String(255), nullable=False)
    year_2022 = db.Column(db.Integer)
    year_2021 = db.Column(db.Integer)
    year_2020 = db.Column(db.Integer)
    year_2019 = db.Column(db.Integer)