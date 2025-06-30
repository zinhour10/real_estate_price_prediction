import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import time


# Load your training data (the same used for feature selection)
train_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\processed\mockup_dataset_road_min_max.csv')

# Build the lookup table for h_id statistics (use existing columns)
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
# Load roads data ONCE at the top of your file
ROADS_PATH = r"D:\CADT\cambodia-latest-free.shp\gis_osm_roads_free_1.shp"
roads = gpd.read_file(ROADS_PATH)
roads = roads.to_crs(epsg=32648)  # Project to metric CRS for distance calculation

# Define road types to flag
road_types = [
    'bridleway', 'corridor', 'cycleway', 'disused', 'footway', 'motorway', 'path',
    'pedestrian', 'primary', 'residential', 'road', 'secondary', 'service', 'steps',
    'tertiary', 'track', 'trunk', 'trunk_link', 'unclassified', 'unused'
]

def get_road_type_features(lat, lon, distance=500):
    # Create point and project to metric CRS
    point = gpd.GeoDataFrame(
        [{'geometry': Point(lon, lat)}],
        crs='EPSG:4326'
    ).to_crs(epsg=32648)
    # Find roads within distance
    nearby = roads[roads.distance(point.iloc[0].geometry) <= distance]
    features = {}
    for road_type in road_types:
        features[f'f_{road_type}'] = int(road_type in nearby['fclass'].values)
    return features

# Load all reference data ONCE
cafe_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\cafe_location.csv')
gas_station_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\gas_station_location.csv')
hospital_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\hospital_lat_lon.csv')
hotel_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\hotel_lat_lon.csv')
mart_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\mart_lat_lon.csv')
pre_school_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\pre_school_lat_lon.csv')
secondary_school_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\secondary_school_lat_lon.csv')
primary_school_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\primary_school_lat_lon.csv')
university_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\university_lat_lon.csv')
seven_eleven_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\sevenevelen_lat_lon.csv')
resturant_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\resturant_lat_lon.csv')
super_market_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\super_market_lat_lon.csv')
borey_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\borey_lat_lon.csv')
bank_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\bank_lat_lon.csv')
atm_df = pd.read_csv(r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\scrape\atm_lat_lon.csv')
# ...add more as needed

def haversine(lat1, lon1, lats2, lons2):
    R = 6371
    lat1, lon1, lats2, lons2 = map(np.radians, [lat1, lon1, lats2, lons2])
    dlat = lats2 - lat1
    dlon = lons2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lats2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

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

central_places = [
    {"name": "Koh_Pich", "lat": 11.551377, "lon": 104.941998},
    {"name": "Russian_Market", "lat": 11.541022, "lon": 104.914067},
    {"name": "AEON_Mall_1", "lat": 11.5479772, "lon": 104.9323125},
    {"name": "AEON_Mall_2", "lat": 11.5987765, "lon": 104.8825985},
    {"name": "AEON_Mall_3", "lat": 11.4841593, "lon": 104.91524},
    {"name": "Bassac_Lane", "lat": 11.5529714, "lon": 104.9271472},
    {"name": "Koh_Norea", "lat": 11.5441525, "lon": 104.9529025},
    {"name": "Camko_City", "lat": 11.5940666, "lon": 104.8912984},
    {"name": "Olympic_Stadium", "lat": 11.5596514, "lon": 104.90982},
    {"name": "Phsar_Tmey", "lat": 11.569552, "lon": 104.9183331},
    {"name": "Boeng_Keng_Kang_1", "lat": 11.551141, "lon": 104.9228331},
    {"name": "Wat_Phnom", "lat": 11.5759527, "lon": 104.9211453},
    {"name": "Chroy_Changvar_Bridge", "lat": 11.5872047, "lon": 104.9191252},
    {"name": "Vattanac_Tower", "lat": 11.5729518, "lon": 104.9170059},
    {"name": "Royal_Palace", "lat": 11.5638469, "lon": 104.9283975},
    {"name": "Sisowath_Riverside_Park", "lat": 11.5694802, "lon": 104.9316061},
    {"name": "Phnom_Penh_Airport", "lat": 11.5497995, "lon": 104.8375804}
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

# Load population and commune data ONCE at the top of your file
KONTUR_PATH = r"D:\CADT\kontur_population_20231101.gpkg\population_clip_cambodia.gpkg"
COMMUNE_PATH = r"D:\CADT\kontur_population_20231101.gpkg\CambodiaCommune_Fixed.gpkg"

kontur = gpd.read_file(KONTUR_PATH, layer='population_clip_cambodia')
communes = gpd.read_file(COMMUNE_PATH)
kontur = kontur.to_crs(communes.crs)

def get_address_features(lat, lon):
    point_gdf = gpd.GeoDataFrame(
        [{'geometry': Point(lon, lat)}],
        crs=communes.crs
    )
    # Spatial join with communes to get address info
    joined = gpd.sjoin(point_gdf, communes, how='left', predicate='within')
    # Spatial join with kontur to get population info
    joined_pop = gpd.sjoin(point_gdf, kontur, how='left', predicate='within')

    address = {
        'address_line_2': joined.iloc[0]['ADM3_EN'] if not joined.empty else None,
        'address_locality': joined.iloc[0]['ADM2_EN'] if not joined.empty else None,
        'address_subdivision': joined.iloc[0]['ADM1_EN'] if not joined.empty else None,
        'population': joined_pop.iloc[0]['population'] if not joined_pop.empty else None,
        'h_id': joined_pop.iloc[0]['h3'] if not joined_pop.empty and 'h3' in joined_pop.columns else None
    }
    return address

def get_all_features(lat, lon):
    features = {}
    features.update(count_nearby(lat, lon, cafe_df, 'cafe'))
    features.update(count_nearby(lat, lon, gas_station_df, 'gas_station'))
    features.update(count_nearby(lat, lon, hospital_df, 'hospital'))
    features.update(count_nearby(lat, lon, hotel_df, 'hotel'))
    features.update(count_nearby(lat, lon, mart_df, 'mart'))
    features.update(count_nearby(lat, lon, pre_school_df, 'pre_school'))
    features.update(count_nearby(lat, lon, secondary_school_df, 'secondary_school'))
    features.update(count_nearby(lat, lon, primary_school_df, 'primary_school'))
    features.update(count_nearby(lat, lon, university_df, 'university'))
    features.update(count_nearby(lat, lon, seven_eleven_df, 'seven_eleven'))
    features.update(count_nearby(lat, lon, resturant_df, 'resturant'))
    features.update(count_nearby(lat, lon, super_market_df, 'super_market'))
    features.update(count_nearby(lat, lon, borey_df, 'borey'))
    features.update(count_nearby(lat, lon, bank_df, 'bank'))
    features.update(count_nearby(lat, lon, atm_df, 'atm'))
    features.update(get_central_place_features(lat, lon))
    address_features = get_address_features(lat, lon)
    features.update(address_features)
    # Add h3 price stats
    h_id = address_features.get('h_id')
    features.update(get_h_id_price_stats(h_id))
    features.update(get_road_type_features(lat, lon))
    return features

if __name__ == "__main__":
    # Example coordinates (Phnom Penh)
    lat = 11.575445826234887
    lon = 104.92218942164058

    start = time.time()
    features = get_all_features(lat, lon)
    end = time.time()

    for k, v in features.items():
        print(f"{k}: {v}")
    print(f"\nTotal processing time: {end - start:.2f} seconds")