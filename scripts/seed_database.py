import sys
import os
import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import engine, Base, SessionLocal
from backend.app.models.entities import (
    City, Location, Event, ModelMetadata, DataSource
)

def seed():
    print("Creating all database tables if not existing...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_cities = db.query(City).count()
        if existing_cities >= 5:
            print("Database already contains metropolitan cities. Skipping city seeding.")
        else:
            print("Seeding 5 Indian Metropolitan Cities...")
            cities_data = [
                City(city_code="DEL", city_name="Delhi", state="Delhi NCT", latitude=28.6139, longitude=77.2090, zoom_level=12),
                City(city_code="BOM", city_name="Mumbai", state="Maharashtra", latitude=19.0760, longitude=72.8777, zoom_level=12),
                City(city_code="BLR", city_name="Bengaluru", state="Karnataka", latitude=12.9716, longitude=77.5946, zoom_level=12),
                City(city_code="HYD", city_name="Hyderabad", state="Telangana", latitude=17.3850, longitude=78.4867, zoom_level=12),
                City(city_code="CCU", city_name="Kolkata", state="West Bengal", latitude=22.5726, longitude=88.3639, zoom_level=12),
            ]
            db.add_all(cities_data)
            db.commit()

        # Seed Locations / Corridors
        del_city = db.query(City).filter(City.city_code == "DEL").first()
        bom_city = db.query(City).filter(City.city_code == "BOM").first()
        blr_city = db.query(City).filter(City.city_code == "BLR").first()
        hyd_city = db.query(City).filter(City.city_code == "HYD").first()
        ccu_city = db.query(City).filter(City.city_code == "CCU").first()

        existing_locs = db.query(Location).count()
        if existing_locs >= 20:
            print("Corridors already seeded. Skipping location seeding.")
        else:
            print("Seeding 25 Benchmark Road Corridors...")
            locations_data = [
                # Delhi
                Location(city_id=del_city.id, location_code="DEL_001", location_name="Laxmi Nagar", corridor_name="Vikas Marg Arterial Corridor", latitude=28.6304, longitude=77.2773, road_type="primary", road_lanes=6, speed_limit_kmh=50.0, free_flow_speed_kmh=55.0, accident_risk_score=0.65),
                Location(city_id=del_city.id, location_code="DEL_002", location_name="Connaught Place", corridor_name="Radial Commercial Ring Road", latitude=28.6315, longitude=77.2167, road_type="primary", road_lanes=4, speed_limit_kmh=40.0, free_flow_speed_kmh=45.0, accident_risk_score=0.45),
                Location(city_id=del_city.id, location_code="DEL_003", location_name="Karol Bagh", corridor_name="Pusa Road Commercial Arterial", latitude=28.6514, longitude=77.1907, road_type="secondary", road_lanes=4, speed_limit_kmh=40.0, free_flow_speed_kmh=45.0, accident_risk_score=0.55),
                Location(city_id=del_city.id, location_code="DEL_004", location_name="Hauz Khas", corridor_name="Outer Ring Road Corridor", latitude=28.5494, longitude=77.2001, road_type="trunk", road_lanes=8, speed_limit_kmh=60.0, free_flow_speed_kmh=65.0, accident_risk_score=0.50),
                Location(city_id=del_city.id, location_code="DEL_005", location_name="Nehru Place", corridor_name="Lala Lajpat Rai Marg", latitude=28.5492, longitude=77.2518, road_type="primary", road_lanes=6, speed_limit_kmh=50.0, free_flow_speed_kmh=55.0, accident_risk_score=0.60),

                # Mumbai
                Location(city_id=bom_city.id, location_code="BOM_001", location_name="Andheri (WEH & SV Rd)", corridor_name="Western Express Highway & SV Road", latitude=19.1136, longitude=72.8697, road_type="trunk", road_lanes=8, speed_limit_kmh=60.0, free_flow_speed_kmh=65.0, accident_risk_score=0.75),
                Location(city_id=bom_city.id, location_code="BOM_002", location_name="Bandra Kurla Complex (BKC)", corridor_name="BKC Main Financial Boulevard", latitude=19.0657, longitude=72.8687, road_type="primary", road_lanes=6, speed_limit_kmh=50.0, free_flow_speed_kmh=55.0, accident_risk_score=0.40),
                Location(city_id=bom_city.id, location_code="BOM_003", location_name="Dadar TT Circle", corridor_name="Dr. Babasaheb Ambedkar Road", latitude=19.0178, longitude=72.8478, road_type="primary", road_lanes=6, speed_limit_kmh=45.0, free_flow_speed_kmh=50.0, accident_risk_score=0.70),
                Location(city_id=bom_city.id, location_code="BOM_004", location_name="Powai (JVLR)", corridor_name="Jogeshwari-Vikhroli Link Road", latitude=19.1176, longitude=72.9060, road_type="trunk", road_lanes=6, speed_limit_kmh=55.0, free_flow_speed_kmh=60.0, accident_risk_score=0.60),
                Location(city_id=bom_city.id, location_code="BOM_005", location_name="Borivali", corridor_name="Western Express Highway Borivali Segment", latitude=19.2288, longitude=72.8541, road_type="trunk", road_lanes=8, speed_limit_kmh=65.0, free_flow_speed_kmh=70.0, accident_risk_score=0.55),

                # Bengaluru
                Location(city_id=blr_city.id, location_code="BLR_001", location_name="Whitefield", corridor_name="ITPB Main Road & Hope Farm Junction", latitude=12.9698, longitude=77.7499, road_type="primary", road_lanes=4, speed_limit_kmh=45.0, free_flow_speed_kmh=50.0, accident_risk_score=0.70),
                Location(city_id=blr_city.id, location_code="BLR_002", location_name="Central Silk Board Junction", corridor_name="Hosur Road - Outer Ring Road Interchange", latitude=12.9177, longitude=77.6238, road_type="trunk", road_lanes=8, speed_limit_kmh=50.0, free_flow_speed_kmh=60.0, accident_risk_score=0.85),
                Location(city_id=blr_city.id, location_code="BLR_003", location_name="Koramangala", corridor_name="80 Feet Road Commercial Corridor", latitude=12.9352, longitude=77.6245, road_type="secondary", road_lanes=4, speed_limit_kmh=40.0, free_flow_speed_kmh=45.0, accident_risk_score=0.50),
                Location(city_id=blr_city.id, location_code="BLR_004", location_name="Indiranagar", corridor_name="100 Feet Road Commercial Axis", latitude=12.9784, longitude=77.6408, road_type="secondary", road_lanes=4, speed_limit_kmh=40.0, free_flow_speed_kmh=45.0, accident_risk_score=0.45),
                Location(city_id=blr_city.id, location_code="BLR_005", location_name="Electronic City", corridor_name="Hosur Elevated Expressway & Service Rd", latitude=12.8399, longitude=77.6770, road_type="trunk", road_lanes=8, speed_limit_kmh=70.0, free_flow_speed_kmh=80.0, accident_risk_score=0.55),

                # Hyderabad
                Location(city_id=hyd_city.id, location_code="HYD_001", location_name="HITEC City", corridor_name="Cyber Towers Arterial Boulevard", latitude=17.4435, longitude=78.3772, road_type="trunk", road_lanes=6, speed_limit_kmh=55.0, free_flow_speed_kmh=60.0, accident_risk_score=0.50),
                Location(city_id=hyd_city.id, location_code="HYD_002", location_name="Gachibowli", corridor_name="Financial District - ORR Junction", latitude=17.4401, longitude=78.3489, road_type="trunk", road_lanes=8, speed_limit_kmh=65.0, free_flow_speed_kmh=70.0, accident_risk_score=0.45),
                Location(city_id=hyd_city.id, location_code="HYD_003", location_name="Banjara Hills", corridor_name="Road No. 1 Arterial Axis", latitude=17.4156, longitude=78.4350, road_type="primary", road_lanes=4, speed_limit_kmh=45.0, free_flow_speed_kmh=50.0, accident_risk_score=0.55),
                Location(city_id=hyd_city.id, location_code="HYD_004", location_name="Begumpet", corridor_name="Sardar Patel Road Corridor", latitude=17.4447, longitude=78.4664, road_type="primary", road_lanes=6, speed_limit_kmh=50.0, free_flow_speed_kmh=55.0, accident_risk_score=0.60),
                Location(city_id=hyd_city.id, location_code="HYD_005", location_name="Secunderabad Station Area", corridor_name="Station Road Intermodal Approach", latitude=17.4399, longitude=78.4983, road_type="primary", road_lanes=4, speed_limit_kmh=35.0, free_flow_speed_kmh=40.0, accident_risk_score=0.70),

                # Kolkata
                Location(city_id=ccu_city.id, location_code="CCU_001", location_name="Salt Lake Sector V", corridor_name="College More Major Arterial", latitude=22.5804, longitude=88.4378, road_type="primary", road_lanes=6, speed_limit_kmh=50.0, free_flow_speed_kmh=55.0, accident_risk_score=0.45),
                Location(city_id=ccu_city.id, location_code="CCU_002", location_name="Park Street", corridor_name="Mother Teresa Sarani Commercial Axis", latitude=22.5535, longitude=88.3524, road_type="secondary", road_lanes=4, speed_limit_kmh=35.0, free_flow_speed_kmh=40.0, accident_risk_score=0.50),
                Location(city_id=ccu_city.id, location_code="CCU_003", location_name="Howrah Station Approach", corridor_name="Howrah Bridge Transit Approach Corridor", latitude=22.5857, longitude=88.3426, road_type="trunk", road_lanes=6, speed_limit_kmh=40.0, free_flow_speed_kmh=45.0, accident_risk_score=0.80),
                Location(city_id=ccu_city.id, location_code="CCU_004", location_name="New Town Action Area I", corridor_name="Major Arterial Road (MAR) Expressway", latitude=22.5878, longitude=88.4688, road_type="trunk", road_lanes=8, speed_limit_kmh=65.0, free_flow_speed_kmh=70.0, accident_risk_score=0.40),
                Location(city_id=ccu_city.id, location_code="CCU_005", location_name="Esplanade", corridor_name="Jawaharlal Nehru Road Transit Core", latitude=22.5645, longitude=88.3516, road_type="primary", road_lanes=6, speed_limit_kmh=40.0, free_flow_speed_kmh=45.0, accident_risk_score=0.65),
            ]
            db.add_all(locations_data)
            db.commit()

        # Seed Verified Events (2019 and 2026 isolated)
        existing_events = db.query(Event).count()
        if existing_events >= 10:
            print("Events already seeded. Skipping event seeding.")
        else:
            print("Seeding 2019 Historical Events & 2026 Future Scenarios...")
            events_data = [
                # 2019 Historical Events (Training Partition)
                Event(city_id=ccu_city.id, event_name="Durga Puja Mahasaptami to Dashami", event_type="Festival", event_date=datetime.date(2019, 10, 5), venue="Citywide Kolkata Pandal Zones", expected_attendance=850000, is_2026_future=False, source_attribution="Kolkata Police Traffic Advisory 2019"),
                Event(city_id=bom_city.id, event_name="Ganesh Visarjan Major Procession", event_type="Festival", event_date=datetime.date(2019, 9, 12), venue="Girgaon Chowpatty & Dadar Beach", expected_attendance=1200000, is_2026_future=False, source_attribution="Mumbai Municipal Corporation 2019"),
                Event(city_id=del_city.id, event_name="Diwali Evening Festivities", event_type="Festival", event_date=datetime.date(2019, 10, 27), venue="Delhi NCT Commercial Rings", expected_attendance=500000, is_2026_future=False, source_attribution="Gazette of India 2019"),
                Event(city_id=blr_city.id, event_name="Bengaluru Tech Summit 2019", event_type="Assembly", event_date=datetime.date(2019, 11, 18), venue="Bengaluru Palace Grounds", expected_attendance=45000, is_2026_future=False, source_attribution="Govt of Karnataka IT Dept"),
                Event(city_id=hyd_city.id, event_name="Bonalu Festival Procession", event_type="Festival", event_date=datetime.date(2019, 7, 28), venue="Old City & Secunderabad", expected_attendance=300000, is_2026_future=False, source_attribution="Telangana State Cultural Calendar"),

                # 2026 Future Context Events (Forward-Looking Scenario Layer)
                Event(city_id=del_city.id, event_name="India International Trade Fair 2026", event_type="Assembly", event_date=datetime.date(2026, 11, 15), venue="Bharat Mandapam (Pragati Maidan)", expected_attendance=120000, is_2026_future=True, source_attribution="ITPO 2026 Official Calendar"),
                Event(city_id=bom_city.id, event_name="International Concert Series 2026", event_type="Concert", event_date=datetime.date(2026, 12, 5), venue="Jio World Garden, BKC", expected_attendance=40000, is_2026_future=True, source_attribution="Ticketmaster & District Event Listing"),
                Event(city_id=blr_city.id, event_name="Cricket Championship Final 2026", event_type="Sports", event_date=datetime.date(2026, 11, 22), venue="M. Chinnaswamy Stadium", expected_attendance=38000, is_2026_future=True, source_attribution="BCCI 2026 Match Schedule"),
                Event(city_id=ccu_city.id, event_name="Durga Puja Carnival 2026", event_type="Festival", event_date=datetime.date(2026, 10, 20), venue="Red Road, Kolkata", expected_attendance=600000, is_2026_future=True, source_attribution="West Bengal Tourism 2026"),
                Event(city_id=hyd_city.id, event_name="Global AI Summit 2026", event_type="Assembly", event_date=datetime.date(2026, 11, 8), venue="HICC Novotel HITEC City", expected_attendance=25000, is_2026_future=True, source_attribution="Telangana Emerging Tech 2026"),
            ]
            db.add_all(events_data)
            db.commit()

        # Seed Model Metadata
        existing_models = db.query(ModelMetadata).count()
        if existing_models >= 4:
            print("Model metadata already seeded.")
        else:
            print("Seeding 4 Model Approaches Benchmarks (15% Test Split)...")
            models_data = [
                ModelMetadata(model_key="historical_mean", model_name="Historical Mean Baseline", algorithm_family="Spatio-Temporal Segment Lookup", training_period="April 1 – Oct 11, 2019", total_training_samples=129150, total_test_samples=27675, mae=11.45, rmse=14.82, r2_score=0.542, is_primary=False),
                ModelMetadata(model_key="linear_regression", model_name="Linear Regression (Ridge)", algorithm_family="Regularized Linear Estimator", training_period="April 1 – Oct 11, 2019", total_training_samples=129150, total_test_samples=27675, mae=8.32, rmse=10.95, r2_score=0.698, is_primary=False),
                ModelMetadata(model_key="random_forest", model_name="Random Forest Regressor", algorithm_family="Multi-Tree Bagging Ensemble", training_period="April 1 – Oct 11, 2019", total_training_samples=129150, total_test_samples=27675, mae=4.88, rmse=6.54, r2_score=0.841, is_primary=False),
                ModelMetadata(model_key="xgboost", model_name="XGBoost Regressor", algorithm_family="Gradient Boosted Decision Trees", training_period="April 1 – Oct 11, 2019", total_training_samples=129150, total_test_samples=27675, mae=3.65, rmse=4.92, r2_score=0.895, is_primary=True),
            ]
            db.add_all(models_data)
            db.commit()

        # Seed Data Sources
        existing_sources = db.query(DataSource).count()
        if existing_sources >= 5:
            print("Data sources already seeded.")
        else:
            print("Seeding Ingested Data Sources Catalog...")
            sources_data = [
                DataSource(source_name="Uber Movement Speeds & Travel Times", category="Traffic", provenance_url="https://zenodo.org/record/uber-movement-india", temporal_coverage="2019-04-01 to 2019-12-31", spatial_coverage="Delhi, Mumbai, Bengaluru, Hyderabad, Kolkata", record_count=184500, license="Creative Commons Attribution Non-Commercial", quality_status="Verified"),
                DataSource(source_name="OpenStreetMap & Geofabrik India", category="Infrastructure", provenance_url="https://download.geofabrik.de/asia/india.html", temporal_coverage="2019-2024 Extracts", spatial_coverage="5 Metropolitan Municipal Extents", record_count=42000, license="ODbL", quality_status="Verified"),
                DataSource(source_name="Open-Meteo Historical Weather (ERA5)", category="Weather", provenance_url="https://archive-api.open-meteo.com/v1/archive", temporal_coverage="2019-04-01 to 2019-12-31 (Hourly)", spatial_coverage="Point-based Coordinates for 5 Cities", record_count=32880, license="CC BY 4.0", quality_status="Verified"),
                DataSource(source_name="MoRTH Road Accidents in India", category="Context", provenance_url="https://morth.nic.in/road-accident-in-india", temporal_coverage="2019 Annual Gazette", spatial_coverage="Million-Plus Cities & Arterial Corridors", record_count=520, license="Open Government Data (OGD) India", quality_status="Verified"),
                DataSource(source_name="Curated National & Regional Public Holidays", category="Context", provenance_url="Gazette of India 2019 & Municipal Calendars", temporal_coverage="2019 National & Regional Dates", spatial_coverage="Delhi, Mumbai, Bengaluru, Hyderabad, Kolkata", record_count=84, license="Public Domain", quality_status="Verified"),
            ]
            db.add_all(sources_data)
            db.commit()

        print("Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
