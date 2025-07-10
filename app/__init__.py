from flask import Flask
from .routes import map_routes

import pandas as pd
import os

CSV_FILE_PATH = r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\processed\mockup_dataset_road_min_max.csv'
global_train_df = pd.DataFrame() # Initialize as empty

if os.path.exists(CSV_FILE_PATH):
    try:
        global_train_df = pd.read_csv(CSV_FILE_PATH)
        print("CSV loaded successfully into global_train_df!")
    except Exception as e:
        print(f"Error loading CSV at startup: {e}")
else:
    print(f"CSV file not found at: {CSV_FILE_PATH}. Please check the path.")


def create_app():
    app = Flask(__name__)
    map_routes(app, global_train_df)
    return app