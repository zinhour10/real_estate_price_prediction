from flask import render_template, request, jsonify
from .utils import create_folium_map
from .shared import stored_coords
from .pipeline import get_features_for_current_coords, predict_with_model, model
from .features import get_all_features

last_prediction = {}  # <-- Define at module level

def map_routes(app):
    @app.route("/")
    def index():
        create_folium_map()  # Create or update the map
        return render_template("index.html")

    @app.route("/store-coord", methods=["POST"])
    def store_coord():
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        stored_coords['lat'] = lat
        stored_coords['lon'] = lon
        print(f"Received: lat={lat}, lon={lon}")
        return jsonify({'status': 'success', 'lat': lat, 'lon': lon})

    @app.route("/get-features", methods=["GET"])
    def get_features_get():
        try:
            lat = stored_coords.get('lat')
            lon = stored_coords.get('lon')
            if lat is None or lon is None:
                return jsonify({"error": "Coordinates not set"}), 400
            features = get_all_features(lat, lon)
            return jsonify(features)  # Return all features
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/last-prediction", methods=["GET"])
    def get_last_prediction():
        if not last_prediction:
            return jsonify({"error": "No prediction made yet"}), 400
        return jsonify(last_prediction)

    @app.route("/run-model", methods=["GET"])
    def run_model():
        global last_prediction  # Only one global statement, at the top!
        try:
            land_area_str = request.args.get("land_area")
            if not land_area_str:
                if not last_prediction:
                    return jsonify({"error": "No prediction made yet"}), 400
                return jsonify(last_prediction)
            land_area = float(land_area_str)
            lat = stored_coords.get('lat')
            lon = stored_coords.get('lon')
            if lat is None or lon is None:
                return jsonify({"error": "Coordinates not set"}), 400
            y_pred = predict_with_model(model)
            price = land_area * y_pred
            price_lower = price * 0.9
            price_upper = price * 1.1
            last_prediction = {
                "price_per_m2": y_pred,
                "land_area": land_area,
                "price": price,
                "lat": lat,
                "lon": lon,
                "price_range": [price_lower, price_upper]
            }
            return jsonify(last_prediction)
        except Exception as e:
            return jsonify({"error": str(e)}), 400