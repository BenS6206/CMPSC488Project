# # # my_project/routes.py
# # from flask import Blueprint, render_template, request, redirect, url_for
# # from .models import MyArea
# # from .database import db
# # import os
# # import geopandas as gpd
# # from geoalchemy2.shape import from_shape
# #
# # main_blueprint = Blueprint('main', __name__)
# #
# # @main_blueprint.route('/')
# # def index():
# #     # Renders a page with an OpenStreetMap (Leaflet)
# #     return render_template('index.html')
# #
# # @main_blueprint.route('/areas')
# # def list_areas():
# #     # Query all MyArea entries from the database
# #     areas = MyArea.query.all()
# #     return render_template('areas.html', areas=areas)
# #
# # @main_blueprint.route('/upload', methods=['GET', 'POST'])
# # def upload():
# #     if request.method == 'POST':
# #         file = request.files.get('file')
# #         if not file:
# #             return "No file uploaded", 400
# #
# #         filename = file.filename
# #         filepath = os.path.join('data', filename)
# #         file.save(filepath)
# #
# #         if filename.endswith('.geojson'):
# #             # Read .geojson using GeoPandas
# #             gdf = gpd.read_file(filepath)
# #
# #             # For each feature, create a MyArea record
# #             for idx, row in gdf.iterrows():
# #                 name = row.get('name', f"Feature_{idx}")
# #                 population = row.get('population', 0)
# #                 geometry = row.geometry
# #
# #                 if geometry:
# #                     geom_wkb = from_shape(geometry, srid=4326)
# #                 else:
# #                     geom_wkb = None
# #
# #                 area = MyArea(
# #                     name=name,
# #                     population=population,
# #                     geom=geom_wkb
# #                 )
# #                 db.session.add(area)
# #
# #             db.session.commit()
# #
# #         elif filename.endswith('.csv'):
# #             # TODO: Implement CSV parsing if needed
# #             # Example: read CSV with lat/lon or WKT columns, etc.
# #             pass
# #
# #         # Clean up the file to avoid storing permanently
# #         os.remove(filepath)
# #         return redirect(url_for('main.list_areas'))
# #     else:
# #         # If GET, show a simple upload form
# #         return render_template('upload.html')
# #
# #
#
# # my_project/routes.py
# from flask import Blueprint, render_template, request
# import pandas as pd
#
# main_blueprint = Blueprint('main', __name__)
#
# # Load the Excel file once at startup (adjust the file path)
# EXCEL_FILE_PATH = "data/estimation.xlsx"
#
# # Read the Excel file into a DataFrame
# df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
#
# @main_blueprint.route('/search', methods=['GET', 'POST'])
# def search_county():
#     results = None
#     search_term = ""
#
#     if request.method == "POST":
#         search_term = request.form.get("county_name", "").strip().lower()
#         if search_term:
#             # Filter counties that contain the search term (case-insensitive)
#             matches = df[df.iloc[:, 0].astype(str).str.lower().str.contains(search_term, na=False)]
#
#             # If matches found, extract relevant population data
#             if not matches.empty:
#                 results = matches.iloc[:, [0, 1, 2, 3, 4]].to_dict(orient="records")
#
#     return render_template('search.html', results=results, search_term=search_term)


# my_project/routes.py
from flask import Blueprint, render_template, request, jsonify
from .models import MyArea, CensusData
from .database import db
import pandas as pd

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/")
def index():
    return render_template("index.html")

@main_blueprint.route("/areas")
def list_areas():
    areas = MyArea.query.all()
    return render_template("areas.html", areas=areas)

@main_blueprint.route("/search", methods=["GET", "POST"])
def search_county():
    results = None
    search_term = ""

    if request.method == "POST":
        search_term = request.form.get("county_name", "").strip().lower()
        if search_term:
            matches = CensusData.query.filter(CensusData.county.ilike(f"%{search_term}%")).all()
            results = [{"county": row.county, "2022": row.year_2022, "2021": row.year_2021, "2020": row.year_2020, "2019": row.year_2019} for row in matches]

    return render_template("search.html", results=results, search_term=search_term)

@main_blueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            file.save(f"data/{file.filename}")  # Save file to 'data' folder
            return "File uploaded successfully!"

    return render_template("upload.html")