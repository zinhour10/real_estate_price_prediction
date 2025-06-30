from flask import Flask
from .routes import map_routes

def create_app():
    app = Flask(__name__)
    map_routes(app)
    return app