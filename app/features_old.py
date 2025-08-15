import os
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import time
from .shared import stored_coords

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Load your training data ---
train_path = os.path.join(BASE_DIR, "data", "processed", "mockup_dataset_road_min_max.csv")
train_df = pd.read_csv(train_path)

# Build the lookup table for h_id statistics
h_id_stats = (
    train_df.groupby('h_id')[['h_id_price_mean', 'h_id_price_max', 'h_id_price_median', 'h_id_price_min']]
    .first()
)

def get_h_id_price_stats(h_id):
    if pd.isna(h_id) or h_id not in h_id_stats.index:
        return {
            'h_id_price_mean': None,
            'h_id_price_max': None,
            'h_id_price_median': None,
            'h_id_price_min': None
        }
    stats = h_id_stats.loc[h_id]
    return {
        'h_id_price_mean': stats['h_id_price_mean'],
        'h_id_price_max': stats['h_id_price_max'],
        'h_id_price_median': stats['h_id_price_median'],
        'h_id_price_min': stats['h_id_price_min']
    }

# --- Load roads data ---
roads_path = os.path.join(BASE_DIR, "data", "gis", "cambodia-latest-free.shp")
roads = gpd.read_file(roads_path)
roads = roads.to_crs(epsg=32648)  # Project to metric CRS

road_types = [
    'bridleway', 'corridor', 'cycleway', 'disused', 'footway', 'motorway', 'path',
    'pedestrian', 'primary', 'residential', 'road', 'secondary', 'service', 'steps',
    'tertiary', 'track', 'trunk', 'trunk_link', 'unclassified', 'unused'
]

def get_road_type_features(lat, lon, distance=100):
    point = gpd.GeoDataFrame(
        [{'geometry': Point(lon, lat)}],
        crs='EPSG:4326'
    ).to_crs(epsg=32648)
    nearby = roads[roads.distance(point.iloc[0].geometry) <= distance]
    return {f'f_{road_type}': int(road_type in nearby['fclass'].values) for road_type in road_types}

# --- Load all reference data ---
def load_ref_csv(filename):
    return pd.read_csv(os.path.join(BASE_DIR, "data", "raw", "scrape", filename))

cafe_df = load_ref_csv("cafe_location.csv")
gas_station_df = load_ref_csv("gas_station_location.csv")
hospital_df = load_ref_csv("hospital_lat_lon.csv")
hotel_df = load_ref_csv("hotel_lat_lon.csv")
mart_df = load_ref_csv("mart_lat_lon.csv")
pre_school_df = load_ref_csv("pre_school_lat_lon.csv")
secondary_school_df = load_ref_csv("secondary_school_lat_lon.csv")
primary_school_df = load_ref_csv("primary_school_lat_lon.csv")
university_df = load_ref_csv("university_lat_lon.csv")
seven_eleven_df = load_ref_csv("sevenevelen_lat_lon.csv")
resturant_df = load_ref_csv("resturant_lat_lon.csv")
super_market_df = load_ref_csv("super_market_lat_lon.csv")
borey_df = load_ref_csv("borey_lat_lon.csv")
bank_df = load_ref_csv("bank_lat_lon.csv")
atm_df = load_ref_csv("atm_lat_lon.csv")
# Add more as needed

# --- Haversine function ---
def haversine(lat1, lon1, lats2, lons2):
    R = 6371
    lat1, lon1, lats2, lons2 = map(np.radians, [lat1, lon1, lats2, lons2])
    dlat = lats2 - lat1
    dlon = lons2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lats2) * np.sin(dlon/2.0)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def count_nearby(lat, lon, ref_df, prefix):
    lats = ref_df['lat'].values
    lons = ref_df['lon'].values
    dists = haversine(lat, lon, lats, lons)
    return {
        f'n_{prefix}_5km': int(np.sum(dists <= 5)),
        f'nearest_{prefix}': int(np.sum(dists <= 0.5)),
        f'n_{prefix}_in_1km': int(np.sum((dists > 0.5) & (dists <= 1))),
        f'n_{prefix}_in_1km_to_2km': int(np.sum((dists > 1) & (dists <= 2))),
        f'n_{prefix}_in_2km_to_3km': int(np.sum((dists > 2) & (dists <= 3))),
        f'n_{prefix}_in_3km_to_5km': int(np.sum((dists > 3) & (dists <= 5))),
    }

# --- Central places ---
central_places = [
    {"name": "Koh_Pich", "lat": 11.551377, "lon": 104.941998},
    {"name": "Russian_Market", "lat": 11.541022, "lon": 104.914067},
    {"name": "AEON_Mall_1", "lat": 11.5479772, "lon": 104.9323125},
    # ... add all others
]

def get_central_place_features(lat, lon):
    features = {}
    for place in central_places:
        d = haversine(lat, lon, place['lat'], place['lon'])
        name = place['name']
        features[f"near_{name}_in_km"] = float(d)
        features[f"{name}_nearest"] = int(d <= 1)
        features[f"{name}_1_2km"] = int(1 < d <= 2)
        features[f"{name}_2_3km"] = int(2 < d <= 3)
        features[f"{name}_3_5km"] = int(3 < d <= 5)
        features[f"{name}_5_10km"] = int(5 < d <= 10)
    return features

# --- Population and commune data ---
kontur_path = os.path.join(BASE_DIR, "data", "kontur", "population_clip_cambodia.gpkg")
commune_path = os.path.join(BASE_DIR, "data", "kontur", "CambodiaCommune_Fixed.gpkg")

kontur = gpd.read_file(kontur_path, layer='population_clip_cambodia')
communes = gpd.read_file(commune_path)
kontur = kontur.to_crs(communes.crs)

def get_address_features(lat, lon):
    point_gdf = gpd.GeoDataFrame([{'geometry': Point(lon, lat)}], crs=communes.crs)
    joined = gpd.sjoin(point_gdf, communes, how='left', predicate='within')
    joined_pop = gpd.sjoin(point_gdf, kontur, how='left', predicate='within')

    return {
        'address_line_2': joined.iloc[0]['ADM3_EN'] if not joined.empty else None,
        'address_locality': joined.iloc[0]['ADM2_EN'] if not joined.empty else None,
        'address_subdivision': joined.iloc[0]['ADM1_EN'] if not joined.empty else None,
        'population': joined_pop.iloc[0]['population'] if not joined_pop.empty else None,
        'h_id': joined_pop.iloc[0]['h3'] if not joined_pop.empty and 'h3' in joined_pop.columns else None
    }

# --- Aggregate features ---
def get_all_features(lat, lon):
    features = {}
    for df, prefix in [
        (cafe_df, 'cafe'), (gas_station_df, 'gas_station'), (hospital_df, 'hospital'),
        (hotel_df, 'hotel'), (mart_df, 'mart'), (pre_school_df, 'pre_school'),
        (secondary_school_df, 'secondary_school'), (primary_school_df, 'primary_school'),
        (university_df, 'university'), (seven_eleven_df, 'seven_eleven'),
        (resturant_df, 'resturant'), (super_market_df, 'super_market'),
        (borey_df, 'borey'), (bank_df, 'bank'), (atm_df, 'atm')
    ]:
        features.update(count_nearby(lat, lon, df, prefix))

    features.update(get_central_place_features(lat, lon))
    address_features = get_address_features(lat, lon)
    features.update(address_features)
    features.update(get_h_id_price_stats(address_features.get('h_id')))
    features.update(get_road_type_features(lat, lon))
    features['latitude'] = lat
    features['longitude'] = lon
    return features
