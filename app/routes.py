from flask import render_template, session, request, jsonify, Response, make_response, send_file, current_app
from .utils import create_folium_map, create_folium_map_for_detial, create_folium_map_for_batch_detail
from .shared import stored_coords
from .pipeline import get_features_for_current_coords, predict_with_model, model, predict_batch_with_model
from .features import get_all_features
from .find_neighbour import get_neighbour, get_neighbours
from .to_pdf import generate_property_valuation_pdf
import pandas as pd
from io import BytesIO
import os
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

last_prediction = {}
latest_batch_results = []
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def map_routes(app, train_df_param: pd.DataFrame):
    # Helper function to get features as dict
    def get_features_data():
        try:
            lat = stored_coords.get('lat')
            lon = stored_coords.get('lon')
            if lat is None or lon is None:
                logger.error("Coordinates not set when fetching features")
                return {}
            return get_all_features(lat, lon)
        except Exception as e:
            logger.error(f"Error getting features: {str(e)}")
            return {}

    # Helper function to get prediction as number
    def get_prediction_data():
        global last_prediction
        if not last_prediction:
            logger.warning("No prediction available")
            return {}
        return last_prediction

    # Helper function to get nearby properties as list
    def get_nearby_data():
        try:
            nearby = get_neighbours(train_df_param, 3)
            if nearby.empty:
                return []
            
            # Skip the first row (target property) and convert to list of dicts
            return nearby.iloc[1:].to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error getting nearby properties: {str(e)}")
            return []

    @app.route("/detail")
    def detail():
        create_folium_map_for_detial()
        return render_template("detail.html")
    
    @app.route("/batch_detail")
    def batch_details():
        create_folium_map_for_batch_detail()
        return render_template("batch_detail.html")
    
    @app.route("/")
    def index():
        create_folium_map()
        return render_template("index.html")
    
    @app.route("/neighbour")
    def neighbour():
        neighbour_data_df = get_neighbour(train_df_param)
        if not neighbour_data_df.empty:
            neighbour_json_string = neighbour_data_df.to_json(orient='records', indent=4)
            return Response(neighbour_json_string, mimetype='application/json')
        else:
            return jsonify([])
    
    @app.route('/generate-report')
    def generate_report():
        try:
            logger.info("Starting report generation...")
            
            # Get all required data
            property_data = get_features_data()
            predict = get_prediction_data()
            comparison = get_nearby_data()

            logger.info("Data fetched successfully:")
            # logger.info(f"Property Data keys: {list(property_data.keys())}")
            # logger.info(f"Prediction value: {predict}")
            # logger.info(f"Comparisons count: {len(comparison)}")

            # Prepare logo path
            img_path = os.path.join(current_app.root_path, 'static', 'img', 'wing_logo.png')
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Logo image not found at: {img_path}")
            logger.info(f"Using logo from: {img_path}")

            # Generate PDF
            buffer = BytesIO()
            generate_property_valuation_pdf(
                buffer,
                property_data,
                predict,
                comparison,
                img_path
            )
            buffer.seek(0)
            logger.info("PDF generated successfully")

            # Create response
            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = (
                'attachment; filename=Property_Valuation_Report_'
                f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
            
            return response

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Failed to generate report",
                "message": str(e),
                "details": "Check server logs for more information"
            }), 500

    @app.route("/store-coord", methods=["POST"])
    def store_coord():
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        stored_coords['lat'] = lat
        stored_coords['lon'] = lon
        logger.info(f"Stored coordinates: lat={lat}, lon={lon}")
        return jsonify({'status': 'success', 'lat': lat, 'lon': lon})

    @app.route("/get-features", methods=["GET"])
    def get_features_route():
        try:
            features = get_features_data()
            return jsonify(features)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/last-prediction", methods=["GET"])
    def get_last_prediction_route():
        global last_prediction
        if not last_prediction:
            return jsonify({"error": "No prediction made yet"}), 400
        return jsonify(last_prediction)

    @app.route("/run-model", methods=["GET"])
    def run_model():
        global last_prediction
        print(last_prediction)
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
                
            y_pred = float(predict_with_model(model))
            price = float(land_area * y_pred)
            price_lower = float(price * 0.9)
            price_upper = float(price * 1.1)
            
            last_prediction = {
                "price_per_m2": y_pred,
                "land_area": land_area,
                "price": price,
                "lat": lat,
                "lon": lon,
                "price_range": [price_lower, price_upper]
            }
            
            logger.info(f"New prediction: {last_prediction}")
            return jsonify(last_prediction)
            
        except Exception as e:
            logger.error(f"Model error: {str(e)}")
            return jsonify({"error": str(e)}), 400
            
    @app.route('/nearby-properties', methods=['GET'])
    def get_nearby_properties_route():
        try:
            nearby = get_neighbours(train_df_param, 3)
            
            if nearby.empty:
                return jsonify({
                    "status": "error",
                    "message": "Could not find nearby properties"
                }), 404
            
            # Convert to JSON-friendly format
            result = {
                "target_property": {
                    "h_id": nearby.iloc[0]['h_id'],
                    "latitude": nearby.iloc[0]['latitude'],
                    "longitude": nearby.iloc[0]['longitude']
                },
                "nearby_properties": nearby.iloc[1:].to_dict(orient='records')  # Skip target property
            }
            
            return jsonify({
                "status": "success",
                "count": len(nearby) - 1,  # Exclude target property
                "results": result
            })
            
        except Exception as e:
            logger.error(f"Nearby properties error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
            
    @app.route('/upload', methods=['POST'])
    def upload_csv():
        global latest_batch_results 
        data = request.get_json()  # Requires Content-Type: application/json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        csv_data = data.get('csvData', [])
        cleaned_data = [
            [item.strip('\r') for item in row]
            for row in csv_data
            if len(row) > 1  # Skip empty rows
        ]
        csv_data = cleaned_data.copy()
        # print("Received CSV data:", csv_data)  # Debug
        df = pd.DataFrame(
            [row[:-1] + [row[-1].strip('\r')] for row in csv_data[1:] if row],
            columns=[col.strip('\r') for col in csv_data[0]]
        )
        df['lat'] = pd.to_numeric(df['lat'])
        df['lon'] = pd.to_numeric(df['lon'])
        df['land_area'] = pd.to_numeric(df['land_area'])
        
        feature_dicts = df.apply(
            lambda row: get_all_features(row['lat'], row['lon']), 
            axis=1
        )
        features_df = pd.DataFrame(list(feature_dicts))
        result_df = pd.concat([df['land_area'], features_df], axis=1)
        # print("Received CSV data:", df)
        # result = df.apply(lambda row: {
        #     **row.to_dict(),
        #     **get_all_features(row['lat'], row['lon'])
        # }, axis=1).tolist()
        # print(result)
        # print("==============================================")
        
        # print(result_df)
        
        # Make predictions
        batch_predict = predict_batch_with_model(model, result_df)
        final = batch_predict * result_df['land_area']
        
        # Build response
        result_df['price_per_m2'] = batch_predict
        result_df['price'] = final

        # Convert to JSON format
        response_data = {
            'results': result_df.to_dict(orient='records')  # List of dicts per row
        }
        latest_batch_results = result_df.to_dict(orient='records')


        return jsonify(latest_batch_results)
    @app.route('/get_latest_batch_predictions', methods=['GET'])
    def get_latest_batch_predictions():
        return jsonify({'results': latest_batch_results})
