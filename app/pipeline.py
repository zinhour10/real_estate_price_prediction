try:
    from .shared import stored_coords
    from .features import get_all_features
except ImportError:
    from shared import stored_coords
    from features import get_all_features
import pandas as pd
import joblib

lat = stored_coords.get('lat')
lon = stored_coords.get('lon')

# Update model path to label encoded version
MODEL_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\models\xgboost\xgboost_model_label_v3.joblib"
LABEL_ENCODERS_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\processed\label_encoders.pkl"

model = joblib.load(MODEL_PATH)
label_encoders = joblib.load(LABEL_ENCODERS_PATH)

# Your selected features (should match model training features)
SELECTED_FEATURES = ['Phsar_Chas_nearest', 'Royal_Palace_3_5km', 'address_line_2', 
                     'address_locality', 'h_id', 'n_atm_in_1km', 'n_atm_in_2km_to_3km', 
                     'n_atm_in_3km_to_5km', 'nearest_resturant', 'h_id_price_min']

def get_features_for_current_coords():
    lat = stored_coords.get('lat')
    lon = stored_coords.get('lon')
    if lat is None or lon is None:
        raise ValueError("No coordinates stored yet.")
    features = get_all_features(lat, lon)
    # Filter only selected features
    filtered = {k: features.get(k) for k in SELECTED_FEATURES}
    return filtered
def predict_with_model(model):
    features = get_features_for_current_coords()
    print("Original features:", features)
    print("Label encoders:", label_encoders)

    # Apply label encoding to categorical features
    encoded_values = {}
    for col, encoder in label_encoders.items():
        if col in features:
            # Handle unseen categories by mapping to a special value
            if features[col] in encoder.classes_:
                encoded_val = encoder.transform([features[col]])[0]
                features[col] = encoded_val
                encoded_values[col] = encoded_val
            else:
                features[col] = -1
                encoded_values[col] = -1

    # Reverse (decode) to check correctness
    for col, encoder in label_encoders.items():
        if col in encoded_values and encoded_values[col] != -1:
            decoded = encoder.inverse_transform([encoded_values[col]])[0]
            print(f"Reverse decoded {col}: {encoded_values[col]} -> {decoded}")
        elif col in encoded_values:
            print(f"Reverse decoded {col}: -1 (unseen category)")

    # Create DataFrame with the correct feature order
    X = pd.DataFrame([features], columns=SELECTED_FEATURES)
    if hasattr(model, 'feature_names_in_'):
        X = X[model.feature_names_in_]
    result = model.predict(X)
    return float(result[0]) 

if __name__ == "__main__":
    try:
        y_pred = predict_with_model(model)
        print("Prediction:", y_pred)
    except Exception as e:
        print("Error during prediction:", e)