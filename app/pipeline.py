try:
    from .shared import stored_coords
    from .features import get_all_features
except ImportError:
    from shared import stored_coords
    from features import get_all_features
import pandas as pd
import joblib
from sklearn.preprocessing import OneHotEncoder

lat = stored_coords.get('lat')
lon = stored_coords.get('lon')


MODEL_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\models\linear_regression\linear_regression_model_v1.joblib"
model = joblib.load(MODEL_PATH)

# Load your training data to fit the encoder
TRAIN_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\processed\mockup_dataset_road_min_max.csv"
train_df = pd.read_csv(TRAIN_PATH)
cat_cols = ['address_line_2']

# Fit the encoder on training data
ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ohe.fit(train_df[cat_cols])



# Your selected features
SELECTED_FEATURES = [
    'address_line_2', 'near_Koh_Pich_in_km', 'near_Russian_Market_in_km', 'near_Boeng_Keng_Kang_1_in_km',
    'n_cafe_5km', 'n_cafe_in_3km_to_5km', 'n_hospital_in_1km_to_2km', 'nearest_hotel', 'n_hotel_in_1km_to_2km',
    'n_hotel_in_3km_to_5km', 'n_mart_in_3km_to_5km', 'n_pre_school_5km', 'n_pre_school_in_1km_to_2km',
    'n_primary_school_in_2km_to_3km', 'n_primary_school_in_3km_to_5km', 'n_university_5km', 'n_university_in_3km_to_5km',
    'n_seven_eleven_5km', 'n_resturant_in_1km', 'n_resturant_in_3km_to_5km', 'n_super_market_in_1km',
    'n_super_market_in_1km_to_2km', 'n_super_market_in_2km_to_3km', 'n_super_market_in_3km_to_5km',
    'nearest_atm', 'n_atm_in_1km', 'n_atm_in_1km_to_2km', 'h_id_price_mean', 'h_id_price_max', 'h_id_price_median'
]

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
    # One-hot encode address_line_2
    address_val = features.pop('address_line_2')
    address_ohe = ohe.transform([[address_val]])
    address_ohe_df = pd.DataFrame(address_ohe, columns=ohe.get_feature_names_out(['address_line_2']))
    # Combine with other features
    num_features = pd.DataFrame([features])
    X = pd.concat([num_features, address_ohe_df], axis=1)
    # Ensure column order and names match model
    X = X.reindex(columns=model.feature_names_in_, fill_value=0)
    result = model.predict(X)
    return result[0]

if __name__ == "__main__":
    try:
        y_pred = predict_with_model(model)
        print("Prediction:", y_pred)
    except Exception as e:
        print("Error during prediction:", e)