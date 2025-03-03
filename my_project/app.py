# my_project/app.py
from flask import Flask
from .config import Config
from .database import db
from .routes import main_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(main_blueprint)

    return app

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)