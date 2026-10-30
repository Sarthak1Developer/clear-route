import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from backend.app.models.entities import (
    City, Location, TrafficRecord, WeatherRecord,
    Event, Prediction, ModelMetadata, DataSource
)

class DataRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_cities(self) -> List[City]:
        return self.db.query(City).order_by(City.id).all()

    def get_city_by_name(self, city_name: str) -> Optional[City]:
        return self.db.query(City).filter(func.lower(City.city_name) == city_name.lower()).first()

    def get_city_by_code(self, city_code: str) -> Optional[City]:
        return self.db.query(City).filter(func.upper(City.city_code) == city_code.upper()).first()

    def get_locations_by_city_id(self, city_id: int) -> List[Location]:
        return self.db.query(Location).filter(Location.city_id == city_id).order_by(Location.id).all()

    def get_location_by_code_or_id(self, loc_identifier: str) -> Optional[Location]:
        if loc_identifier.isdigit():
            return self.db.query(Location).filter(Location.id == int(loc_identifier)).first()
        return self.db.query(Location).filter(
            func.lower(Location.location_code) == loc_identifier.lower()
        ).first()

    def get_events_by_city_name(self, city_name: str = "") -> List[Event]:
        query = self.db.query(Event).join(City)
        if city_name:
            query = query.filter(func.lower(City.city_name) == city_name.lower())
        return query.order_by(Event.event_date).all()

    def get_all_model_metadata(self) -> List[ModelMetadata]:
        return self.db.query(ModelMetadata).order_by(ModelMetadata.id).all()

    def get_all_data_sources(self) -> List[DataSource]:
        return self.db.query(DataSource).order_by(DataSource.id).all()

    def save_prediction(self, pred_data: Dict[str, Any]) -> Prediction:
        prediction = Prediction(
            location_id=pred_data["location_id"],
            prediction_date=pred_data["prediction_date"],
            prediction_hour=pred_data["prediction_hour"],
            model_type=pred_data["model_type"],
            temperature_c=pred_data.get("temperature_c"),
            precipitation_mm=pred_data.get("precipitation_mm"),
            event_present=pred_data.get("event_present", False),
            event_name=pred_data.get("event_name"),
            predicted_congestion_pct=pred_data["predicted_congestion_pct"],
            congestion_category=pred_data["congestion_category"],
            baseline_congestion_pct=pred_data.get("baseline_congestion_pct"),
            shap_attribution_json=pred_data.get("shap_attribution_json"),
        )
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction
