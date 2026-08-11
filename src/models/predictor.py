import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class Predictor:
    def __init__(self, model_path: str, scaler_path: Optional[str] = None):
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path) if scaler_path else None
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.brand_map = None
        self.model_map = None

        self._load_model()
        if self.scaler_path:
            self._load_scaler()

        #Load encoding maps if available
        self._load_encodings()

    def _load_scaler(self):
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {self.scaler_path}")
        self.scaler = joblib.load(self.scaler_path)
        logger.info(f"Scaler loaded from {self.scaler_path}")

        if hasattr(self.model, 'feature_names_in_'):
            self.feature_names = self.model.feature_names_in_.tolist()

    def _load_encodings(self):
        enc_path = self.model_path.parent / "encodings.pkl"
        #Option 1: Load from saved file
        if enc_path.exists():
            encodings = joblib.load(enc_path)
            self.brand_map = encodings.get('brand_map')
            self.model_map = encodings.get('model_map')
            logger.info("Encodingd loaded from file")

        #Option 2 : Use defaults (for testing)
        if self.brand_map is None:
            self.brand_map = {
                'Tesla': 85000,
                'BMW': 72000,
                'Audi': 68000,
                'Mercedes': 75000,
                'Porsche': 120000,
                'Nissan': 45000,
                'Hyundai': 48000,
                'Kia': 42000,
                'Volkswagen': 50000,
                'Ford': 52000,
                'Toyota': 46000,
                'Volvo': 62000,
                'Jaguar': 78000,
                'Land Rover': 82000,
                'Lamborghini': 200000,
                'Acura': 60000,
                'NIO': 65000
            }

        if self.model_map is None:
            self.model_map = {
                'Model 3': 80000,
                'Model S': 95000,
                'Model X': 100000,
                'Model Y': 85000,
                'X5': 75000,
                'e-tron': 75000,
                'Leaf': 35000,
                'Ioniq 5': 50000,
                'EV6': 48000,
                'ID.4': 48000,
                'Mustang Mach-E': 55000,
                'Taycan': 110000,
                'ET7': 70000
            }

    def _get_encoding(self, value: str, map_dict: Dict, default: float =60000) -> float:
        if not map_dict:
            return default
        return map_dict.get(value,default)

    def transform_input(self, raw_input: Dict) -> pd.DataFrame:
        #Extract and validate inputs
        brand = raw_input.get('brand', 'Unknown')
        model = raw_input.get('model', 'Unknown')
        battery = float(raw_input.get('battery', 60))
        autonomy = float(raw_input.get('autonomy', 400))
        safety = float(raw_input.get('safety', 4.0))
        year = int(raw_input.get('year', 2024))
        autonomous_level = float(raw_input.get('autonomous_level', 2.0))

        current_year = 2026
        vehicle_age = current_year - year

        #Get encodings
        brand_enc = self._get_encoding(brand, self.brand_map, 60000)
        model_enc = self._get_encoding(model, self.model_map, 65000)

        #Feature engineering
        efficiency_score = safety / (battery + 1e-6)

        #Build feature vector
        features = {
            'Year': year,
            'Battery_Capacity_kWh': battery,
            'Range_km': autonomy,
            'Charge_Time_hr': 8.0,
            'Autonomous_Level': autonomous_level,
            'Safety_Rating': safety,
            'Warranty_Years': 4,
            'Vehicle_Age': vehicle_age,
            'Efficiency_Score': efficiency_score,
            'Brand_Enc': brand_enc,
            'Model_Enc': model_enc
        }

        #Create DataFrame with correct column order
        df = pd.DataFrame([features])

        #Ensure column order matches training
        if self.feature_names:
            df = df[self.feature_names]

        #Handle NaN/Inf
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(df.median())

        return df
        
    def predict(self, raw_input: Dict) -> Tuple[float, Dict]:
        try:
            #Transform input
            df = self.transform_input(raw_input)

            #Scale if scaler
            if self.scaler:
                X_scaled = self.scaler.transform(df)
            else:
                X_scaled = df.values

            #Predict
            prediction = self.model.predict(X_scaled)[0]

            #Ensure non-negative
            price = max(5000, float(prediction))

            metadata = {
                'features': df.iloc[0].to_dict(),
                'model_type': type(self.model).__name__
            }

            return price, metadata

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise ValueError(f"Prediction failed: {str(e)}")

    def predict_batch(self, inputs: List[Dict]) -> List[Dict]:
        results = []
        for inp in inputs:
            price, meta = self.predict(inp)
            results.append({
                'input': inp,
                'price': price,
                'metadata': meta
            })
        return results

_predictor_instance = None

def get_predictor(
        model_path: str = "models/artifacts/xgboost_model.pkl",
        scaler_path: str = "models/artifacts/scaler.pkl"
) -> Predictor:

    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = Predictor(model_path, scaler_path)
    return _predictor_instance