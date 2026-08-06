import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
from pathlib import Path
import logging

# setup module-level logger
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, raw_data_path: str, current_year: int = 2026):
        self.raw_dataa_path = Path(raw_data_path)
        self.current_year = current_year
        self.df: Optional[pd.DataFrame] = None
        self.brand_map: Dict[str, float] = {}
        self.global_avg_price: float = 0.0

        #validate input path exista
        if not self.raw_data_path.exists():
            raise FileNotFoundError(f"Raw data not found at: {self.raw_data_path}")

        logger.info(f"DataPipeline initialized with data path: {self.raw_data_path}")
    
    def load_data(self) -> pd.DataFrame:
        logger.info("Loading raw data...")
        self.df = pd.read_csv(self.raw_data_path, encoding = 'latin-1')

        if self.df.empty:
            raise ValueError("Loaded DataFrame is empty. Check the input file.")

        logger.info(f"Loaded {len(self.df)} rows and {len(self.df.columns)} columns.")
        return self.df
    
    def clean_data(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

            logger.info("Cleaning data...")
            initial rows = len(self.df)

            #Remove duplicate rows
            self.df.drop_duplicate(inplace=True)
            duplicates_removed = initial_rows - len(self.df)
            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed} duplicate rows.")

            #Handle missing values in key numeric columns
            #Autonomous_Level
            self.df['Autonomous_Level'] = self.df['Autonomous_Level'].fillna(0)

            #Safety_Rating: fill with median to avoid skewing
            self.df['Safety_Rating'] = self.df['Safety_Rating'].fillna(self.df['Safety_Rating'].median())

            #Ensure correct data types
            self.df['Year'] = self.df['Year'].astype(int)
            self.df['Warranty_Years'] = self.df['Warranty_Years'].astype(int)

            #Drop rows with any remaining NaN critical columns
            critical_cols = ['Price_USD', 'Battery_Capacity_kWh', 'Range_km', 'Charge_Time_hr']
            self.df.dropna(subset=critical_cols, inplace=True)

            rows_dropped = initial_rows - len(self.df) - duplicates_removed
            if rows_dropped > 0:
                logger.warning(f"Dropped {rows_dropped} rows due to missing critical values.")

                logger.info(f"Cleaned data: {len(self.df)} rows remaining.")
                return self.df
            
            def engineer_features(self) -> pd.DataFrame:
                if self.df is None:
                    raise ValueError("Datanot loaded. Call load_data() first.")
                    
                logger.info("Engineering features...")

                #Vehicle Age
                self.df['Vehicle_Age'] = self.current_year - self.df['Year']
                logger.debug("Added 'Vehicle_Age' feature.")

                #Efficiency Score (range per kWh)
                epsilon = 1e-6
                self.df['Efficiency_Score'] = self.df['Range_km'] / (self.df['Battery_Capacity_kWh'] + epsilon)
                logger.debug("Added 'Efficency_Score' feature.")

                #Target Encoding for Brand
                self.brand_map = self.df.groupby('Manufacturer')['Price_USD'].mean().to_dict()
                self.df['Brand_Enc'] = self.df['Model'].map(self.model_map)

                #Target Encoding for Model
                self.model_map = self.df.groupby('Model')['Price_USD'].mean().to_dict()
                self.df['Model_Enc'] = self.df['Model'].map(self.model_map)

                #Store global average as fallback
                self.global_avg_price = self.df['Price_USD'].mean()

                logger.info(f"Feature engineering complete. Total features: {len(self.df.columns)}")
                return self.df

            def get_train_test_split(
                self,
                test_size: float = 0.2,
                random_state: int = 42,
                target_col: str = 'Price_USD'
            ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:

                from sklearn.model_selection import train_test_split

                if self.df is None:
                    raise ValueError("Data not loaded. Call load_data(), clean_data(), engineer_features() first.")

                    exclude_cols = [target_col, 'Manufacturer', 'Model', 'Vehicle_ID', 'Color', 'Country_of_Manufacture.']
                    feature_cols = [col for col in self.df.columns if col not in exclude_cols and self.df[col].dtype in ['int64', 'float64']]

                    if not feature_cols:
                        raise ValueError("No numeric feature columns found. Check data processing.")

                        X = self.df[feture_cols]
                        y = self.df[target_col]

                        logger.info(f"Splitting data with test_size={test_size}. Features: {len(feature_cols)}")
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size, random_state=random_state, shuffle=True
                        )
                        logger.info(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")
                        return X_train, X_test, y_train, y_test

                    def save_processed_data(self, output_path: str) -> None:
                        if self.df is None:
                            raise ValueError("No data to save. Run the pipeline first.")
                        output_path = Path(output_path)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        self.df.to_csv(output_path, index=False)
                        logger.info(f"Processed data saved to: {output_path}")
                    
                    def get_encodings(self) -> Tuple[Dict[str, float], Dict[str, float], float]:
                        if not self.brand_map or not self.model_map:
                            raise ValueError("Encoding not generated. Run engineer_features() first.")
                        return self.brand_map, self.model_map, self.global_avg_price
