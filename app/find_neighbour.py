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

# def get_neighbours(df_param: pd.DataFrame):
#     """
#     Finds ALL properties within 1km radius of target property
    
#     Args:
#         df_param (pd.DataFrame): Property DataFrame with lat/lon columns
    
#     Returns:
#         pd.DataFrame: All properties within 1km radius, 
#                      with distance in km and all original columns
#                      Includes target property as first row (distance=0)
#     """
#     try:
#         # Get target property from API
#         response = requests.get('http://127.0.0.1:5000/get-features', timeout=5)
#         response.raise_for_status()
#         target = response.json()
        
#         # Validate response
#         if not all(k in target for k in ['h_id', 'latitude', 'longitude']):
#             print("Error: API response missing required fields")
#             return pd.DataFrame()
        
#         # Find target in DataFrame
#         target_df = df_param[df_param['h_id'] == target['h_id']]
#         if target_df.empty:
#             print(f"Warning: h_id {target['h_id']} not found in DataFrame")
#             return pd.DataFrame()
        
#         # Get target coordinates
#         target_row = target_df.iloc[0]
#         t_lat = target_row['latitude']
#         t_lon = target_row['longitude']
        
#         # Calculate distances to all properties in meters
#         df_param = df_param.copy()
#         df_param['distance_m'] = df_param.apply(
#             lambda row: haversine(t_lon, t_lat, row['longitude'], row['latitude']) * 1000,
#             axis=1
#         )
        
#         # Filter properties within exactly 1000m (1km) radius
#         nearby = df_param[df_param['distance_m'] <= 1000]
        
#         # Convert back to km for display and sort
#         nearby['distance_km'] = nearby['distance_m'] / 1000
#         nearby = nearby.sort_values('distance_m')
        
#         return nearby.drop(columns=['distance_m'])

#     except requests.exceptions.Timeout:
#         print("Error: API request timed out")
#         return pd.DataFrame()
#     except requests.exceptions.RequestException as e:
#         print(f"Network error: {e}")
#         return pd.DataFrame()
#     except ValueError:
#         print("Error: Invalid JSON response")
#         return pd.DataFrame()
#     except KeyError as e:
#         print(f"Missing column in data: {e}")
#         return pd.DataFrame()



def get_neighbours(df_param: pd.DataFrame, max_distance_km=0.5):
    """
    Finds ALL properties within specified distance (default 1km) of target property
    
    Args:
        df_param (pd.DataFrame): Property DataFrame with lat/lon columns
        max_distance_km (float): Maximum distance in kilometers (default 1km)
    
    Returns:
        pd.DataFrame: All nearby properties within distance threshold, 
                     with distance in km and all original columns
                     Includes target property as first row
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
        # Get target coordinates
        t_lat = target['latitude']
        t_lon = target['longitude']
        
        # Calculate distances to all properties
        df_param = df_param.copy()
        df_param['distance_km'] = df_param.apply(
            lambda row: haversine(t_lon, t_lat, row['longitude'], row['latitude']),
            axis=1
        )
        
        # Filter properties within specified distance (including target)
        nearby = df_param[df_param['distance_km'] <= max_distance_km]
        
        # Sort by distance (target will be first with distance 0)
        nearby = nearby.sort_values('distance_km')
        
        return nearby

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

import pandas as pd
import requests

def get_neighbours_param(df_param: pd.DataFrame, target_feature: dict, max_distance_km=0.5):
    """
    Finds ALL properties within specified distance of target property
    
    Args:
        df_param (pd.DataFrame): Property DataFrame with lat/lon columns
        target_feature (dict): Dictionary with target property details (must include 'latitude', 'longitude')
        max_distance_km (float): Maximum distance in kilometers (default 0.5km)
    
    Returns:
        pd.DataFrame: All nearby properties within distance threshold,
                      with distance in km and all original columns.
                      Includes target property as first row (if in dataset).
    """
    try:
        # Validate input dictionary
        if not all(k in target_feature for k in ['latitude', 'longitude']):
            print("Error: target_feature missing required fields 'latitude' and/or 'longitude'")
            return pd.DataFrame()

        # Get target coordinates
        t_lat = target_feature['latitude']
        t_lon = target_feature['longitude']
        
        # Calculate distances to all properties
        df_param = df_param.copy()
        df_param['distance_km'] = df_param.apply(
            lambda row: haversine(t_lon, t_lat, row['longitude'], row['latitude']),
            axis=1
        )
        
        # Filter properties within specified distance (including target)
        nearby = df_param[df_param['distance_km'] <= max_distance_km]
        
        # Sort by distance (target will be first with distance 0 if it's in the dataset)
        nearby = nearby.sort_values('distance_km')
        
        return nearby

    except KeyError as e:
        print(f"Missing column in data: {e}")
        return pd.DataFrame()

def get_nearby_properties_data(train_df_param):
    try:
        nearby = get_neighbours(train_df_param, 0.5)
        if nearby.empty:
            return {
                "status": "error",
                "message": "Could not find nearby properties"
            }
        result = {
            "target_property": {
                "h_id": nearby.iloc[0]['h_id'],
                "latitude": nearby.iloc[0]['latitude'],
                "longitude": nearby.iloc[0]['longitude']
            },
            "nearby_properties": nearby.iloc[1:].to_dict(orient='records')
        }
        return {
            "status": "success",
            "count": len(nearby) - 1,
            "results": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# def get_neighbours(df_param: pd.DataFrame, max_distance_km=1.0, n_neighbours=1000):
#     """
#     Finds properties within specified distance (default 1km) of target property
    
#     Args:
#         df_param (pd.DataFrame): Property DataFrame with lat/lon columns
#         max_distance_km (float): Maximum distance in kilometers (default 1km)
#         n_neighbours (int): Maximum number of neighbours to return (default 10)
    
#     Returns:
#         pd.DataFrame: Nearby properties within distance threshold, 
#                      with distance in km and all original columns
#                      Includes target property as first row
#     """
#     try:
#         # Get target property from API
#         response = requests.get('http://127.0.0.1:5000/get-features', timeout=5)
#         response.raise_for_status()
#         target = response.json()
        
#         # Validate response
#         if not all(k in target for k in ['h_id', 'latitude', 'longitude']):
#             print("Error: API response missing required fields")
#             return pd.DataFrame()
        
#         # Find target in DataFrame
#         target_df = df_param[df_param['h_id'] == target['h_id']]
#         if target_df.empty:
#             print(f"Warning: h_id {target['h_id']} not found in DataFrame")
#             return pd.DataFrame()
        
#         # Get target coordinates
#         target_row = target_df.iloc[0]
#         t_lat = target_row['latitude']
#         t_lon = target_row['longitude']
        
#         # Calculate distances to all properties
#         df_param = df_param.copy()
#         df_param['distance_km'] = df_param.apply(
#             lambda row: haversine(t_lon, t_lat, row['longitude'], row['latitude']),
#             axis=1
#         )
        
#         # Filter properties within 1km (including target)
#         nearby = df_param[df_param['distance_km'] <= max_distance_km]
        
#         # Sort by distance and limit number of results
#         nearby = nearby.sort_values('distance_km')
        
#         # Return target + nearest neighbors (up to n_neighbours total)
#         return nearby.head(n_neighbours)

#     except requests.exceptions.Timeout:
#         print("Error: API request timed out")
#         return pd.DataFrame()
#     except requests.exceptions.RequestException as e:
#         print(f"Network error: {e}")
#         return pd.DataFrame()
#     except ValueError:
#         print("Error: Invalid JSON response")
#         return pd.DataFrame()
#     except KeyError as e:
#         print(f"Missing column in data: {e}")
#         return pd.DataFrame()





# def get_neighbours(df_param: pd.DataFrame, n_neighbours=10):
#     """
#     Fetches house features from API, finds top 5 nearest properties by coordinates
    
#     Args:
#         df_param (pd.DataFrame): Property DataFrame with lat/lon columns
#         n_neighbours (int): Number of nearest neighbours to return
    
#     Returns:
#         pd.DataFrame: Top 5 nearest properties with distance in km and all original columns
#     """
#     try:
#         # Get target property from API
#         response = requests.get('http://127.0.0.1:5000/get-features', timeout=5)
#         response.raise_for_status()
#         target = response.json()
        
#         # Validate response
#         if not all(k in target for k in ['h_id', 'latitude', 'longitude']):
#             print("Error: API response missing required fields")
#             return pd.DataFrame()
        
#         # Find target in DataFrame
#         target_df = df_param[df_param['h_id'] == target['h_id']]
#         if target_df.empty:
#             print(f"Warning: h_id {target['h_id']} not found in DataFrame")
#             return pd.DataFrame()
        
#         # Get target coordinates
#         target_row = target_df.iloc[0]
#         t_lat = target_row['latitude']
#         t_lon = target_row['longitude']
        
#         # Calculate distances to all properties
#         df_param = df_param.copy()
#         df_param['distance_km'] = df_param.apply(
#             lambda row: haversine(t_lon, t_lat, row['longitude'], row['latitude']),
#             axis=1
#         )
        
#         # Exclude target property and get nearest neighbours
#         neighbours = df_param[df_param['h_id'] != target['h_id']]
#         neighbours = neighbours.sort_values('distance_km').head(n_neighbours)
        
#         # Return all columns including the new distance_km column
#         return neighbours

#     except requests.exceptions.Timeout:
#         print("Error: API request timed out")
#         return pd.DataFrame()
#     except requests.exceptions.RequestException as e:
#         print(f"Network error: {e}")
#         return pd.DataFrame()
#     except ValueError:
#         print("Error: Invalid JSON response")
#         return pd.DataFrame()
#     except KeyError as e:
#         print(f"Missing column in data: {e}")
#         return pd.DataFrame()