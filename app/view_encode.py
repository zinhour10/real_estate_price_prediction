LABEL_ENCODERS_PATH = r"D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\processed\label_encoders.pkl"
import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder

# Load the array of class labels from the .pkl file
with open(LABEL_ENCODERS_PATH, 'rb') as f:
    classes_array = pickle.load(f)
    

file_path = LABEL_ENCODERS_PATH
try:
    with open(file_path, 'rb') as f:
        loaded_data = pickle.load(f)
    print("Data loaded successfully:")
    print(loaded_data)
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
except Exception as e:
    print(f"An error occurred while loading the pickle file: {e}")

# Rebuild LabelEncoder
le = LabelEncoder()
le.fit(classes_array)

# Show Original → Encoded mapping
print("Original → Encoded:")
for original in le.classes_:
    encoded = le.transform([original])[0]
    print(f"{original} → {encoded}")