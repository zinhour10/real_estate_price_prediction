import pandas as pd
import requests
from math import radians, sin, cos, sqrt, atan2

def get_neighbour(df_param: pd.DataFrame):
    """
    Fetches house features from an external API and matches them with a row in the provided DataFrame.

    Args:
        df_param (pd.DataFrame): The DataFrame to search for the matching house ID.

    Returns:
        pd.DataFrame: A DataFrame containing the matched row, or an empty DataFrame if no match or an error occurs.
    """
    try:
        # Make a request to your local API to get house features
        my_house = requests.get('http://127.0.0.1:5000/get-features', timeout=5) # Added timeout for robustness
        my_house.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = my_house.json() # Parse the JSON response

        h_id = data.get('h_id') # Extract the house ID

        if h_id is not None:
            # Filter the provided DataFrame (df_param) for the matching h_id
            matched_row = df_param[df_param['h_id'] == h_id]
            if not matched_row.empty:
                return matched_row
            else:
                print(f"Warning: No matching row found for h_id: {h_id} in the provided DataFrame.")
                return pd.DataFrame() # Return empty DataFrame if no match found
        else:
            print("Error: 'h_id' not found in the response from the API.")
            return pd.DataFrame() # Return empty DataFrame if h_id is missing
    except requests.exceptions.Timeout as e:
        print(f"Error: Request to API timed out: {e}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return pd.DataFrame()
    except ValueError:
        print("Error: Could not decode JSON from the API response.")
        return pd.DataFrame()
def haversine(lon1, lat1, lon2, lat2):
    # Convert degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371  # Earth radius in kilometers
    return c * r

def get_neighbours(df_param: pd.DataFrame, n_neighbours=10):
    """
    Fetches house features from API, finds top 5 nearest properties by coordinates
    
    Args:
        df_param (pd.DataFrame): Property DataFrame with lat/lon columns
        n_neighbours (int): Number of nearest neighbours to return
    
    Returns:
        pd.DataFrame: Top 5 nearest properties with distance in km and all original columns
    """
    try:
        # Get target property from API
        response = requests.get('http://127.0.0.1:5000/get-features', timeout=5)
        response.raise_for_status()
        target = response.json()
        
        # Validate response
        if not all(k in target for k in ['h_id', 'latitude', 'longitude']):
            print("Error: API response missing required fields")
            return pd.DataFrame()
        
        # Find target in DataFrame
        target_df = df_param[df_param['h_id'] == target['h_id']]
        if target_df.empty:
            print(f"Warning: h_id {target['h_id']} not found in DataFrame")
            return pd.DataFrame()
        
        # Get target coordinates
        target_row = target_df.iloc[0]
        t_lat = target_row['latitude']
        t_lon = target_row['longitude']
        
        # Calculate distances to all properties
        df_param = df_param.copy()
        df_param['distance_km'] = df_param.apply(
            lambda row: haversine(t_lon, t_lat, row['longitude'], row['latitude']),
            axis=1
        )
        
        # Exclude target property and get nearest neighbours
        neighbours = df_param[df_param['h_id'] != target['h_id']]
        neighbours = neighbours.sort_values('distance_km').head(n_neighbours)
        
        # Return all columns including the new distance_km column
        return neighbours

    except requests.exceptions.Timeout:
        print("Error: API request timed out")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return pd.DataFrame()
    except ValueError:
        print("Error: Invalid JSON response")
        return pd.DataFrame()
    except KeyError as e:
        print(f"Missing column in data: {e}")
        return pd.DataFrame()