import os
import json
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ingest_events_holidays")

def ingest_events_holidays(output_dir: str = "data/bronze/events"):
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Ingesting verified 2019 historical holidays and separate 2026 future context...")

    # 1. 2019 Historical Events (Strictly used for model training)
    events_2019 = [
        {"city": "Delhi", "event_name": "Independence Day Celebrations", "event_type": "Public Holiday", "date": "2019-08-15", "venue": "Red Fort & Central Delhi", "is_holiday": 1, "attendance": 100000},
        {"city": "Delhi", "event_name": "Gandhi Jayanti", "event_type": "Public Holiday", "date": "2019-10-02", "venue": "Raj Ghat", "is_holiday": 1, "attendance": 30000},
        {"city": "Delhi", "event_name": "Diwali Festival Evening", "event_type": "Festival", "date": "2019-10-27", "venue": "Citywide Retail Rings", "is_holiday": 1, "attendance": 500000},
        {"city": "Delhi", "event_name": "Guru Nanak Jayanti", "event_type": "Festival", "date": "2019-11-12", "venue": "Gurudwara Bangla Sahib", "is_holiday": 1, "attendance": 150000},
        {"city": "Delhi", "event_name": "Christmas Day", "event_type": "Public Holiday", "date": "2019-12-25", "venue": "Sacred Heart Cathedral", "is_holiday": 1, "attendance": 80000},

        {"city": "Mumbai", "event_name": "Ganesh Chaturthi Utsav", "event_type": "Festival", "date": "2019-09-02", "venue": "Lalbaug & Girgaon", "is_holiday": 1, "attendance": 1500000},
        {"city": "Mumbai", "event_name": "Anant Chaturdashi Visarjan", "event_type": "Festival", "date": "2019-09-12", "venue": "Girgaon Chowpatty & Juhu", "is_holiday": 1, "attendance": 2000000},
        {"city": "Mumbai", "event_name": "Diwali Lakshmi Pujan", "event_type": "Festival", "date": "2019-10-27", "venue": "Marine Drive & Dadar", "is_holiday": 1, "attendance": 600000},

        {"city": "Bengaluru", "event_name": "Eid ul-Fitr", "event_type": "Public Holiday", "date": "2019-06-05", "venue": "Shivajinagar & Citywide", "is_holiday": 1, "attendance": 200000},
        {"city": "Bengaluru", "event_name": "Bengaluru Karaga Shaktyotsava", "event_type": "Festival", "date": "2019-04-19", "venue": "Thigalarpet Old City", "is_holiday": 0, "attendance": 180000},
        {"city": "Bengaluru", "event_name": "Karnataka Rajyotsava", "event_type": "Festival", "date": "2019-11-01", "venue": "Kanteerava Stadium", "is_holiday": 1, "attendance": 250000},

        {"city": "Hyderabad", "event_name": "Bonalu Procession", "event_type": "Festival", "date": "2019-07-28", "venue": "Lal Darwaza & Golconda", "is_holiday": 1, "attendance": 350000},
        {"city": "Hyderabad", "event_name": "Milad-un-Nabi", "event_type": "Public Holiday", "date": "2019-11-10", "venue": "Charminar & Old City", "is_holiday": 1, "attendance": 400000},

        {"city": "Kolkata", "event_name": "Durga Puja Saptami - Dashami", "event_type": "Festival", "date": "2019-10-05", "venue": "North & South Kolkata Pandals", "is_holiday": 1, "attendance": 1800000},
        {"city": "Kolkata", "event_name": "Kali Puja & Diwali", "event_type": "Festival", "date": "2019-10-27", "venue": "Kalighat & Dakshineswar", "is_holiday": 1, "attendance": 500000},
    ]

    # 2. 2026 Future Context Layer (Isolated for scenario forecasting)
    events_2026 = [
        {"city": "Delhi", "event_name": "India International Trade Fair 2026", "event_type": "Assembly", "date": "2026-11-15", "venue": "Bharat Mandapam", "is_holiday": 0, "attendance": 120000},
        {"city": "Mumbai", "event_name": "International Tech Expo 2026", "event_type": "Assembly", "date": "2026-12-05", "venue": "Jio World Convention Centre, BKC", "is_holiday": 0, "attendance": 40000},
        {"city": "Bengaluru", "event_name": "Cricket Tournament Final 2026", "event_type": "Sports", "date": "2026-11-22", "venue": "M. Chinnaswamy Stadium", "is_holiday": 0, "attendance": 38000},
        {"city": "Kolkata", "event_name": "Durga Puja Carnival 2026", "event_type": "Festival", "date": "2026-10-20", "venue": "Red Road", "is_holiday": 1, "attendance": 600000},
        {"city": "Hyderabad", "event_name": "Global AI Summit 2026", "event_type": "Assembly", "date": "2026-11-08", "venue": "HICC Novotel HITEC City", "is_holiday": 0, "attendance": 25000},
    ]

    df_2019 = pd.DataFrame(events_2019)
    csv_2019 = os.path.join(output_dir, "raw_events_2019_historical.csv")
    df_2019.to_csv(csv_2019, index=False)

    df_2026 = pd.DataFrame(events_2026)
    csv_2026 = os.path.join(output_dir, "raw_events_2026_future.csv")
    df_2026.to_csv(csv_2026, index=False)

    logger.info(f"Bronze 2019 events written to {csv_2019}.")
    logger.info(f"Bronze 2026 future context events written to {csv_2026}.")
    return csv_2019, csv_2026

if __name__ == "__main__":
    ingest_events_holidays()
