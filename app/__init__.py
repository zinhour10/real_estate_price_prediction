import os
import pandas as pd
from .routes import map_routes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_CSV = os.path.join(BASE_DIR, '..', 'data', 'processed', 'land_dataset_final_v2.csv')
global_train_df = pd.read_csv(TRAIN_CSV)

def create_app():
    from flask import Flask
    app = Flask(__name__)
    map_routes(app, global_train_df)
    return app