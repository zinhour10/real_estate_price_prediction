try:
    from .shared import stored_coords
    from .features_old import get_all_features
except ImportError:
    from shared import stored_coords
    from app.features_old import get_all_features
import pandas as pd
import joblib
from sklearn.preprocessing import OneHotEncoder

lat = stored_coords.get('lat')
lon = stored_coords.get('lon')


MODEL_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\models\random_forest\random_forest_model_v4_one_hot.joblib"
model = joblib.load(MODEL_PATH)

# Load your training data to fit the encoder
TRAIN_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\preprocessed\selected_features_onehot_encoded.csv"
train_df = pd.read_csv(TRAIN_PATH)
cat_cols = ['address_line_2', 'address_locality', 'h_id']

# Fit the encoder on training data
# ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
# ohe.fit(train_df[cat_cols])



# Your selected features
SELECTED_FEATURES = ['Phsar_Chas_nearest', 'Royal_Palace_3_5km', 'address_line_2', 'address_locality', 'h_id', 'n_atm_in_1km', 'n_atm_in_2km_to_3km', 'n_atm_in_3km_to_5km', 'nearest_resturant', 'price_per_m2_min']

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
    # List your categorical columns
    # categorical_cols = cat_cols
    
    # Pop categorical values in order
    # cat_values = [features.pop(col) for col in categorical_cols]
    # One-hot encode all categorical columns at once
    # cat_ohe = ohe.transform([cat_values])
    # cat_ohe_df = pd.DataFrame(cat_ohe, columns=ohe.get_feature_names_out(categorical_cols))

    # Combine with other features
    num_features = pd.DataFrame([features])
    # X = pd.concat([num_features, cat_ohe_df], axis=1)
    # Ensure column order and names match model
    X = num_features
    X = X.reindex(columns=model.feature_names_in_, fill_value=0)
    result = model.predict(X)
    return result[0]

if __name__ == "__main__":
    try:
        y_pred = predict_with_model(model)
        print("Prediction:", y_pred)
    except Exception as e:
        print("Error during prediction:", e)