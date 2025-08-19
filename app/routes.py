import os
import json
import csv
import ast
import logging
import statistics
from io import BytesIO
from datetime import datetime

import pandas as pd
from flask import (
    render_template, request, jsonify, Response, make_response,
    current_app, url_for
)

from .utils import create_folium_map, create_folium_map_for_detial, create_folium_map_for_batch_detail
from .shared import stored_coords
from .pipeline import predict_with_model, model, predict_batch_with_model
from .features import get_all_features
from .find_neighbour import get_neighbours, get_neighbours_param
from .to_pdf import generate_property_valuation_pdf, generate_property_valuation_pdf_batch

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Global state
# ---------------------------------------------------------
last_prediction = {}
latest_batch_results = []
features = {}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def get_latest_batch_predictions_data():
        return {'results': latest_batch_results}
    
def get_features_data():
    """Fetch features for stored coords and update global features."""
    global features
    try:
        lat = stored_coords.get('lat')
        lon = stored_coords.get('lon')
        if lat is None or lon is None:
            logger.error("Coordinates not set when fetching features")
            return {}
        features = get_all_features(lat, lon)
        return features
    except Exception as e:
        logger.error(f"Error getting features: {str(e)}")
        return {}

def get_nearby_properties_logic(train_df, radius=0.5):
    """Return nearby properties with target property separated."""
    try:
        nearby = get_neighbours(train_df, radius)
        if nearby.empty:
            return {"error": "Could not find nearby properties"}

        result = {
            "target_property": {
                "h_id": nearby.iloc[0]['h_id'],
                "latitude": nearby.iloc[0]['latitude'],
                "longitude": nearby.iloc[0]['longitude']
            },
            "nearby_properties": nearby.iloc[1:].to_dict(orient='records')
        }
        return {"count": len(nearby) - 1, "results": result}
    except Exception as e:
        return {"error": str(e)}


def run_model_logic(land_area=None):
    """Core model prediction logic, reused by routes."""
    global last_prediction
    lat = stored_coords.get('lat')
    lon = stored_coords.get('lon')

    if lat is None or lon is None:
        return {"error": "Coordinates not set"}

    y_pred = float(predict_with_model(model))

    if land_area is None:
        if not last_prediction:
            return {"error": "No prediction made yet"}
        return last_prediction

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
    return last_prediction


def save_to_csv(data, filename='last_prediction.csv'):
    """Append predictions to CSV, dropping price_range if present."""
    df_new = pd.DataFrame([data])

    if 'price_range' in df_new.columns:
        df_new = df_new.drop(columns=['price_range'])

    if os.path.exists(filename):
        df_existing = pd.read_csv(filename)
        if 'price_range' in df_existing.columns:
            df_existing = df_existing.drop(columns=['price_range'])
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(filename, index=False)
    else:
        df_new.to_csv(filename, index=False)


# ---------------------------------------------------------
# Routes registration
# ---------------------------------------------------------
def map_routes(app, train_df_param: pd.DataFrame):
    @app.route("/")
    def index():
        create_folium_map()
        return render_template("index.html")

    @app.route("/detail")
    def detail():
        run_model_logic()
        create_folium_map_for_detial(train_df_param)
        return render_template("detail.html")

    @app.route("/batch_detail")
    def batch_details():
        create_folium_map_for_batch_detail()
        return render_template("batch_detail.html")

    @app.route('/receive-min-max', methods=['POST'])
    def receive_min_max():
        data = request.get_json()
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        return jsonify({'status': 'success', 'min_price': min_price, 'max_price': max_price})

    @app.route("/get-features", methods=["GET"])
    def get_features_route():
        return jsonify(get_features_data())

    @app.route("/last-prediction", methods=["GET"])
    def get_last_prediction_route():
        global last_prediction
        property_data = get_features_data()
        if not last_prediction:
            return jsonify({"error": "No prediction made yet"}), 400
        return jsonify({**property_data, **last_prediction})

    @app.route("/run-model", methods=["GET"])
    def run_model():
        land_area_str = request.args.get("land_area")
        land_area = float(land_area_str) if land_area_str else None
        result = run_model_logic(land_area)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)

    @app.route("/store-coord", methods=["POST"])
    def store_coord():
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        stored_coords['lat'] = lat
        stored_coords['lon'] = lon
        return jsonify({'status': 'success', 'lat': lat, 'lon': lon})

    @app.route("/save-prediction", methods=["POST"])
    def save_prediction():
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400
        save_to_csv(data)
        return jsonify({"message": "Prediction saved to CSV", "redirect": url_for("index")})

    @app.route("/save-prediction-batch", methods=["POST"])
    def save_prediction_batch():
        data = request.json
        for result in data['results']:
            save_to_csv(result)
        return jsonify({"message": "Prediction saved to CSV", "redirect": url_for("index")})

    @app.route("/neighbour")
    def neighbour():
        neighbour_data_df = get_neighbours(train_df_param, 0.5)
        if not neighbour_data_df.empty:
            return Response(neighbour_data_df.to_json(orient='records', indent=4), mimetype='application/json')
        return jsonify([])

    @app.route('/nearby-properties', methods=['GET'])
    def get_nearby_properties_route():
        result = get_nearby_properties_logic(train_df_param, radius=0.5)
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400
        return jsonify({"status": "success", **result})

    @app.route('/upload', methods=['POST'])
    def upload_csv():
        global latest_batch_results
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        csv_data = data.get('csvData', [])
        cleaned_data = [
            [item.strip('\r') for item in row] for row in csv_data if len(row) > 1
        ]
        if not cleaned_data:
            return jsonify({'error': 'No valid data rows found'}), 400

        headers = [col.strip('\r') for col in cleaned_data[0]]
        all_results = []

        for row in cleaned_data[1:]:
            try:
                row_df = pd.DataFrame([row], columns=headers)
                row_df['lat'] = pd.to_numeric(row_df['lat'], errors='coerce')
                row_df['lon'] = pd.to_numeric(row_df['lon'], errors='coerce')
                row_df['land_area'] = pd.to_numeric(row_df['land_area'], errors='coerce')

                if row_df[['lat', 'lon', 'land_area']].isnull().any().any():
                    continue

                features_local = {
                    k: v for k, v in get_all_features(
                        row_df['lat'].iloc[0], row_df['lon'].iloc[0]
                    ).items() if pd.notna(v) and v is not None
                }
                row_data = {
                    k: v for k, v in row_df.iloc[0].to_dict().items()
                    if pd.notna(v) and v is not None
                }
                result_dict = {**row_data, **features_local}

                try:
                    prediction_df = pd.concat([row_df['land_area'], pd.DataFrame([features_local])], axis=1)
                    batch_predict = predict_batch_with_model(model, prediction_df)
                    final_price = batch_predict * row_df['land_area'].iloc[0]
                    if pd.notna(batch_predict[0]):
                        result_dict.update({
                            'price_per_m2': float(batch_predict[0]),
                            'price': float(final_price[0])
                        })
                except Exception as e:
                    logger.warning(f"Prediction failed for row: {str(e)}")

                cleaned_result = {
                    k: v for k, v in result_dict.items()
                    if pd.notna(v) and v is not None and v != ''
                }
                if cleaned_result:
                    all_results.append(cleaned_result)
            except Exception as e:
                logger.warning(f"Skipping row due to error: {str(e)}")
                continue

        latest_batch_results = all_results
        return jsonify(all_results)

    @app.route('/get_latest_batch_predictions', methods=['GET'])
    def get_latest_batch_predictions():
        return jsonify({'results': latest_batch_results})
    @app.route('/generate-report')
    def generate_report():
        try:
            logger.info("Starting report generation...")
            
            # Get all required data
            property_data = get_features_data()
            predict = run_model_logic()
            comparison = get_nearby_properties_logic(train_df_param)
            # print(comparison)
            # print(predict)
            # if "error" in comparison:
            #     return jsonify({"error": comparison["error"]}), 400

            nearby_list = comparison["results"]["nearby_properties"] 
            # if not nearby_list:
            #     return jsonify({"error": "No nearby properties found"}), 400

            min_price_item = min(nearby_list, key=lambda x: x['price_per_m2'])
            max_price_item = max(nearby_list, key=lambda x: x['price_per_m2'])

            min_price = min_price_item['price_per_m2']
            max_price = max_price_item['price_per_m2']

            prices = [item['price_per_m2'] for item in nearby_list]
            median_price = statistics.median(prices)
            mean_price = statistics.mean(prices)
            predicted_price = predict['price_per_m2']

            
            # print("Min price_per_m2:", min_price)
            # print("Max price_per_m2:", max_price)
            # print("Median price_per_m2:", median_price)
            # print("Mean price_per_m2:", mean_price)
            #dist = distant
            price_range = max_price - min_price
            dist_median = abs(predicted_price - median_price)
            dist_mean = abs(predicted_price - mean_price)
            #weight that we set think that importance
            w1, w2, w3 = 0.4, 0.4, 0.2
        
            if mean_price == 0:
                confidence = 0
            else:
                score = 1 - (w1 * dist_median + w2 * dist_mean + w3 * price_range) / mean_price
                confidence = max(0, min(score * 100, 100))  # clamp between 0 and 100%

            # print(f"Confidence Level: {confidence:.2f}%")

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
                nearby_list,
                confidence,
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
            
    
    
    @app.route('/generate-report-batch', methods=['POST'])
    def generate_report_batch():
        logger.info("🚀 Step 1: Batch PDF generation started")
        
        data = request.json
        if not data or 'results' not in data:
            logger.error("❌ Step 2: Invalid input data format")
            return jsonify({"error": "Invalid data format"}), 400

        generated_files = []

        for index, result in enumerate(data['results']):
            try:
                property_data = result
                comparison = get_neighbours_param(train_df_param, property_data)
                if isinstance(comparison, list):
                    comparison = pd.DataFrame(comparison)
                min_price_item = comparison.loc[comparison['price_per_m2'].idxmin()]
                max_price_item = comparison.loc[comparison['price_per_m2'].idxmax()]

                min_price = min_price_item['price_per_m2']
                max_price = max_price_item['price_per_m2']

                prices = comparison['price_per_m2'].tolist()
                median_price = statistics.median(prices)
                mean_price = statistics.mean(prices)
                predicted_price = property_data['price_per_m2']

                
                # print("Min price_per_m2:", min_price)
                # print("Max price_per_m2:", max_price)
                # print("Median price_per_m2:", median_price)
                # print("Mean price_per_m2:", mean_price)
                #dist = distant
                price_range = max_price - min_price
                dist_median = abs(predicted_price - median_price)
                dist_mean = abs(predicted_price - mean_price)
                #weight that we set think that importance
                w1, w2, w3 = 0.4, 0.4, 0.2
            
                if mean_price == 0:
                    confidence = 0
                else:
                    score = 1 - (w1 * dist_median + w2 * dist_mean + w3 * price_range) / mean_price
                    confidence = max(0, min(score * 100, 100))  # clamp between 0 and 100%

                    
                valid_comparison = [row.to_dict() for _, row in comparison.iterrows()]
                # print("Data Valid Comparison",valid_comparison)
                logo_path = os.path.join(current_app.root_path, 'static', 'img', 'wing_logo.png')
                buffer = BytesIO()
                generate_property_valuation_pdf_batch(
                    buffer,
                    property_data,
                    valid_comparison,
                    confidence,
                    logo_path
                )
                pdf_filename = f"report_{index}.pdf"
                output_path = os.path.join("static", "reports", pdf_filename)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                generated_files.append(pdf_filename)

            except Exception as e:
                logger.error(f"Failed to generate PDF for item {index}: {e}", exc_info=True)
                continue
        return jsonify({
            "message": f"{len(generated_files)} reports generated successfully.",
            "reports": generated_files,
            "redirect": url_for("index")
        })
