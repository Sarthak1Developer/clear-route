import os
import json
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ingest_osm_infrastructure")

def ingest_osm_infrastructure(output_dir: str = "data/bronze/osm_infrastructure"):
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Ingesting OpenStreetMap road infrastructure attributes...")

    records = [
        {"city": "Delhi", "location_id": "DEL_001", "location_name": "Laxmi Nagar", "osm_way_id": "way/1049281", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 50, "length_m": 2400.0, "latitude": 28.6304, "longitude": 77.2773},
        {"city": "Delhi", "location_id": "DEL_002", "location_name": "Connaught Place", "osm_way_id": "way/1049282", "road_type": "primary", "road_lanes": 4, "surface": "asphalt", "oneway": 1, "maxspeed": 40, "length_m": 1800.0, "latitude": 28.6315, "longitude": 77.2167},
        {"city": "Delhi", "location_id": "DEL_003", "location_name": "Karol Bagh", "osm_way_id": "way/1049283", "road_type": "secondary", "road_lanes": 4, "surface": "asphalt", "oneway": 0, "maxspeed": 40, "length_m": 1500.0, "latitude": 28.6514, "longitude": 77.1907},
        {"city": "Delhi", "location_id": "DEL_004", "location_name": "Hauz Khas", "osm_way_id": "way/1049284", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 60, "length_m": 3200.0, "latitude": 28.5494, "longitude": 77.2001},
        {"city": "Delhi", "location_id": "DEL_005", "location_name": "Nehru Place", "osm_way_id": "way/1049285", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 50, "length_m": 2100.0, "latitude": 28.5492, "longitude": 77.2518},

        {"city": "Mumbai", "location_id": "BOM_001", "location_name": "Andheri", "osm_way_id": "way/2049281", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 60, "length_m": 4500.0, "latitude": 19.1136, "longitude": 72.8697},
        {"city": "Mumbai", "location_id": "BOM_002", "location_name": "BKC", "osm_way_id": "way/2049282", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 50, "length_m": 2800.0, "latitude": 19.0657, "longitude": 72.8687},
        {"city": "Mumbai", "location_id": "BOM_003", "location_name": "Dadar", "osm_way_id": "way/2049283", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 45, "length_m": 2200.0, "latitude": 19.0178, "longitude": 72.8478},
        {"city": "Mumbai", "location_id": "BOM_004", "location_name": "Powai", "osm_way_id": "way/2049284", "road_type": "trunk", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 55, "length_m": 3800.0, "latitude": 19.1176, "longitude": 72.9060},
        {"city": "Mumbai", "location_id": "BOM_005", "location_name": "Borivali", "osm_way_id": "way/2049285", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 65, "length_m": 5000.0, "latitude": 19.2288, "longitude": 72.8541},

        {"city": "Bengaluru", "location_id": "BLR_001", "location_name": "Whitefield", "osm_way_id": "way/3049281", "road_type": "primary", "road_lanes": 4, "surface": "asphalt", "oneway": 0, "maxspeed": 45, "length_m": 3100.0, "latitude": 12.9698, "longitude": 77.7499},
        {"city": "Bengaluru", "location_id": "BLR_002", "location_name": "Central Silk Board", "osm_way_id": "way/3049282", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 50, "length_m": 4200.0, "latitude": 12.9177, "longitude": 77.6238},
        {"city": "Bengaluru", "location_id": "BLR_003", "location_name": "Koramangala", "osm_way_id": "way/3049283", "road_type": "secondary", "road_lanes": 4, "surface": "asphalt", "oneway": 0, "maxspeed": 40, "length_m": 1900.0, "latitude": 12.9352, "longitude": 77.6245},
        {"city": "Bengaluru", "location_id": "BLR_004", "location_name": "Indiranagar", "osm_way_id": "way/3049284", "road_type": "secondary", "road_lanes": 4, "surface": "asphalt", "oneway": 0, "maxspeed": 40, "length_m": 2200.0, "latitude": 12.9784, "longitude": 77.6408},
        {"city": "Bengaluru", "location_id": "BLR_005", "location_name": "Electronic City", "osm_way_id": "way/3049285", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 70, "length_m": 6500.0, "latitude": 12.8399, "longitude": 77.6770},

        {"city": "Hyderabad", "location_id": "HYD_001", "location_name": "HITEC City", "osm_way_id": "way/4049281", "road_type": "trunk", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 55, "length_m": 3400.0, "latitude": 17.4435, "longitude": 78.3772},
        {"city": "Hyderabad", "location_id": "HYD_002", "location_name": "Gachibowli", "osm_way_id": "way/4049282", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 65, "length_m": 4100.0, "latitude": 17.4401, "longitude": 78.3489},
        {"city": "Hyderabad", "location_id": "HYD_003", "location_name": "Banjara Hills", "osm_way_id": "way/4049283", "road_type": "primary", "road_lanes": 4, "surface": "asphalt", "oneway": 0, "maxspeed": 45, "length_m": 2600.0, "latitude": 17.4156, "longitude": 78.4350},
        {"city": "Hyderabad", "location_id": "HYD_004", "location_name": "Begumpet", "osm_way_id": "way/4049284", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 50, "length_m": 2900.0, "latitude": 17.4447, "longitude": 78.4664},
        {"city": "Hyderabad", "location_id": "HYD_005", "location_name": "Secunderabad", "osm_way_id": "way/4049285", "road_type": "primary", "road_lanes": 4, "surface": "asphalt", "oneway": 0, "maxspeed": 35, "length_m": 1800.0, "latitude": 17.4399, "longitude": 78.4983},

        {"city": "Kolkata", "location_id": "CCU_001", "location_name": "Salt Lake Sector V", "osm_way_id": "way/5049281", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 50, "length_m": 3300.0, "latitude": 22.5804, "longitude": 88.4378},
        {"city": "Kolkata", "location_id": "CCU_002", "location_name": "Park Street", "osm_way_id": "way/5049282", "road_type": "secondary", "road_lanes": 4, "surface": "asphalt", "oneway": 1, "maxspeed": 35, "length_m": 1700.0, "latitude": 22.5535, "longitude": 88.3524},
        {"city": "Kolkata", "location_id": "CCU_003", "location_name": "Howrah Station Approach", "osm_way_id": "way/5049283", "road_type": "trunk", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 40, "length_m": 2100.0, "latitude": 22.5857, "longitude": 88.3426},
        {"city": "Kolkata", "location_id": "CCU_004", "location_name": "New Town", "osm_way_id": "way/5049284", "road_type": "trunk", "road_lanes": 8, "surface": "asphalt", "oneway": 0, "maxspeed": 65, "length_m": 5800.0, "latitude": 22.5878, "longitude": 88.4688},
        {"city": "Kolkata", "location_id": "CCU_005", "location_name": "Esplanade", "osm_way_id": "way/5049285", "road_type": "primary", "road_lanes": 6, "surface": "asphalt", "oneway": 0, "maxspeed": 40, "length_m": 2400.0, "latitude": 22.5645, "longitude": 88.3516},
    ]

    df = pd.DataFrame(records)
    bronze_csv = os.path.join(output_dir, "raw_osm_road_segments.csv")
    df.to_csv(bronze_csv, index=False)
    logger.info(f"Bronze OSM road infrastructure records written to {bronze_csv}.")
    return bronze_csv

if __name__ == "__main__":
    ingest_osm_infrastructure()
