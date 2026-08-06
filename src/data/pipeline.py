import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self, raw_data_path: str, current_year: int = 2026):
        self.raw_data_path = Path(raw_data_path)
        self.current_year = current_year
        self.df: Optional[pd.DataFrame] = None
        self.brand_map: Dict[str, float] = {}
        self.model_map: Dict[str, float] = {}
        self.global_avg_price: float = 0.0

        if not self.raw_data_path.exists():
            raise FileNotFoundError(f"Raw data not found at: {self.raw_data_path}")

        logger.info("DataPipeline initialized with %s", self.raw_data_path)

    def load_data(self) -> pd.DataFrame:
        """Load CSV and perform cleaning step."""
        logger.info("Loading data from %s", self.raw_data_path)
        self.df = pd.read_csv(self.raw_data_path)
        if self.df is None or self.df.empty:
            raise ValueError("Loaded DataFrame is empty. Check the input file.")

        # Clean immediately so downstream methods can assume consistent state
        self.clean_data()
        return self.df

    def clean_data(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        logger.info("Cleaning data (%d rows)", len(self.df))

        # Remove exact duplicate rows
        before = len(self.df)
        self.df = self.df.drop_duplicates().reset_index(drop=True)
        dup_removed = before - len(self.df)
        if dup_removed > 0:
            logger.info("Removed %d duplicate rows", dup_removed)

        # Fill sensible defaults for missing numeric fields
        if 'Autonomous_Level' in self.df.columns:
            self.df['Autonomous_Level'] = self.df['Autonomous_Level'].fillna(0)

        if 'Safety_Rating' in self.df.columns:
            # fill with median if available otherwise 0
            median = self.df['Safety_Rating'].median()
            if pd.isna(median):
                median = 0
            self.df['Safety_Rating'] = self.df['Safety_Rating'].fillna(median)

        # Ensure integer columns are correct where applicable
        if 'Year' in self.df.columns:
            self.df['Year'] = self.df['Year'].astype(int)
        if 'Warranty_Years' in self.df.columns:
            self.df['Warranty_Years'] = self.df['Warranty_Years'].astype(int)

        # Drop rows missing critical numeric features
        critical_cols = [c for c in ['Price_USD', 'Battery_Capacity_kWh', 'Range_km', 'Charge_Time_hr'] if c in self.df.columns]
        if critical_cols:
            before_drop = len(self.df)
            self.df = self.df.dropna(subset=critical_cols).reset_index(drop=True)
            dropped = before_drop - len(self.df)
            if dropped > 0:
                logger.warning("Dropped %d rows due to missing critical values", dropped)

        logger.info("Cleaned data: %d rows remaining", len(self.df))
        return self.df

    def engineer_features(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        logger.info("Engineering features...")

        # Vehicle age
        if 'Year' in self.df.columns:
            self.df['Vehicle_Age'] = self.current_year - self.df['Year']

        # Efficiency score: range per kWh
        if 'Range_km' in self.df.columns and 'Battery_Capacity_kWh' in self.df.columns:
            eps = 1e-6
            self.df['Efficiency_Score'] = self.df['Range_km'] / (self.df['Battery_Capacity_kWh'] + eps)

        # Target encoding for brand and model
        if 'Manufacturer' in self.df.columns and 'Price_USD' in self.df.columns:
            self.brand_map = self.df.groupby('Manufacturer')['Price_USD'].mean().to_dict()
            self.df['Brand_Enc'] = self.df['Manufacturer'].map(self.brand_map)

        if 'Model' in self.df.columns and 'Price_USD' in self.df.columns:
            self.model_map = self.df.groupby('Model')['Price_USD'].mean().to_dict()
            self.df['Model_Enc'] = self.df['Model'].map(self.model_map)

        if 'Price_USD' in self.df.columns:
            self.global_avg_price = float(self.df['Price_USD'].mean())

        logger.info("Feature engineering complete. Columns: %d", len(self.df.columns))
        return self.df

    def get_train_test_split(self, test_size: float = 0.2, random_state: int = 42, target_col: str = 'Price_USD') -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Return train/test split using pandas (avoids sklearn dependency)."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() and engineer_features() first.")

        exclude = {target_col, 'Manufacturer', 'Model', 'Vehicle_ID', 'Color', 'Country_of_Manufacture'}
        feature_cols = [c for c in self.df.columns if c not in exclude and pd.api.types.is_numeric_dtype(self.df[c])]

        if not feature_cols:
            raise ValueError("No numeric feature columns found. Check data processing.")

        # Shuffle and split
        shuffled = self.df.sample(frac=1, random_state=random_state).reset_index(drop=True)
        n_test = max(1, int(len(shuffled) * test_size))

        test_df = shuffled.iloc[:n_test]
        train_df = shuffled.iloc[n_test:]

        X_train = train_df[feature_cols]
        X_test = test_df[feature_cols]
        y_train = train_df[target_col]
        y_test = test_df[target_col]

        logger.info("Split data: train=%d test=%d", len(X_train), len(X_test))
        return X_train, X_test, y_train, y_test

    def save_processed_data(self, output_path: str) -> None:
        if self.df is None:
            raise ValueError("No data to save. Run the pipeline first.")
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(out, index=False)
        logger.info("Processed data saved to %s", out)

    def get_encodings(self) -> Tuple[Dict[str, float], Dict[str, float], float]:
        return self.brand_map, self.model_map, self.global_avg_price
