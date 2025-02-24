# # my_project/seed_db.py
#
# from shapely.geometry import Polygon
# from geoalchemy2.shape import from_shape
# from .app import create_app
# from .database import db
# from .models import MyArea
#
# def seed_data():
#     """Insert hypothetical polygons into the my_area table."""
#
#     # Define some hypothetical polygons
#     # Example polygon #1
#     poly1 = Polygon([
#         (-90, 30),  # (lng, lat)
#         (-90, 35),
#         (-85, 35),
#         (-85, 30),
#         (-90, 30)
#     ])
#     geom1 = from_shape(poly1, srid=4326)
#
#     # Example polygon #2
#     poly2 = Polygon([
#         (-120, 40),
#         (-120, 45),
#         (-110, 45),
#         (-110, 40),
#         (-120, 40)
#     ])
#     geom2 = from_shape(poly2, srid=4326)
#
#     # Create instances of MyArea
#     area1 = MyArea(
#         name="Hypothetical Region A",
#         population=12345,
#         geom=geom1
#     )
#     area2 = MyArea(
#         name="Hypothetical Region B",
#         population=67890,
#         geom=geom2
#     )
#
#     db.session.add_all([area1, area2])
#     db.session.commit()
#
#
# if __name__ == "__main__":
#     app = create_app()
#     with app.app_context():
#         # Make sure the tables exist (if not already created)
#         db.create_all()
#
#         # Seed the data
#         seed_data()
#
#         print("Database successfully seeded with hypothetical polygons!")
