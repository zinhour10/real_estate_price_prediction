from flask import render_template, request, jsonify
from .utils import create_folium_map
from .shared import stored_coords
from .pipeline import get_features_for_current_coords, predict_with_model, model
from .features import get_all_features

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

    @app.route("/run-model", methods=["GET"])
    def run_model():
        try:
            land_area = float(request.args.get("land_area", 0))            
            y_pred = predict_with_model(model)
            price = land_area * y_pred
            return jsonify(
                prediction=y_pred,
                land_area=land_area,
                price=price
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 400