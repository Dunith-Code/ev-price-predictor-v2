import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
from typing import Dict, Any, Optional, Tuple
import json
import logging
import mlflow.xgboost

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelTrainer:

    def __init__(
            self,
            experiment_name: str = "EV_Price_Prediction",
            model_type: str = "xgboost",
            tracking_uri: Optional[str] = None
        ):

        self.experiment_name = experiment_name
        self.model_type = model_type
        self.run_id = None
        self.best_model = None
        self.best_params = {}
        self.metrics = {}
        self.scaler = None

        #Set MLflow tracking URI
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        #Create or get MLflow experiment
        mlflow.set_experiment(experiment_name)
        logger.info(f"ModelTrainer initialized with experiment '{experiment_name}' and model type '{model_type}'.")

    def _get_model(self, params: Optional[Dict] = None) -> object:
        if params is None:
            params = {}

        models = {
            'linear': LinearRegression,
            'random_forest': RandomForestRegressor,
            'xgboost': XGBRegressor
        }

        model_class = models.get(self.model_type)
        if model_class is None:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        return model_class(**params)

    def _get_default_params(self) -> Dict:
        defaults = {
            'linear': {},
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42,
                'n_jobs': -1
            },
            'xgboost': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 5,
                'random_state': 42,
                'verbosity': 0,
                'n_jobs': -1,
                'tree_method': 'hist'
            }
        }
        return defaults.get(self.model_type, {})

    def _get_param_grid(self) -> Dict:
        grids = {
            'linear': {},
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15],
                'min_samples_split': [2, 5, 10]
            },
            'xgboost': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 1.0]
            }
        }
        return grids.get(self.model_type, {})

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str = 'Price_USD',
        test_size: float = 0.2,
        random_state: int = 42,
        scale_features: bool =True
    ) -> Tuple:
        logger.info("Preparing data for training...")

        #Separate features and target
        exclude_cols = [target_col, 'Manufacturer', 'Model', 'Vehicle_ID', 'Color', 'Country_of_Manufacture']
        feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['int64', 'float64']]

        X = df[feature_cols]
        y = df[target_col]

        #Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, shuffle=True
        )

        #Scale feature if requested
        if scale_features:
            self.scaler = StandardScaler()
            X_train = self.scaler.fit_transform(X_train)
            X_test = self.scaler.transform(X_test)
            logger.info(f"Features scaled using StandardScaler")
        else:
            X_train = X_train.values
            X_test =X_test.values

        logger.info(f"Train: {X_train.shape[0]} rows, Test: {X_test.shape[0]} rows")
        logger.info(f"Features: {feature_cols}")

        return X_train, X_test, y_train, y_test, feature_cols

    def train(
            self,
            X_train: np.ndarray,
            y_train: np.ndarray,
            X_test: np.ndarray,
            y_test: np.ndarray,
            params: Optional[Dict] = None,
            use_grid_search: bool = False
    ) -> Dict:
        logger.info(f"Training {self.model_type} model...")

        if params is None:
            params = self._get_default_params()

        #Start MLflow run
        with mlflow.start_run(run_name=f"{self.model_type}_training") as run:
            self.run_id = run.info.run_id
            logger.info(f"MLflow Run ID: {self.run_id}")

            #Log parameters
            mlflow.log_params(params)

            if use_grid_search and self._get_param_grid():
                logger.info("Performing GridSearchCV for hyperparameter tuning...")
                model = self._get_model()
                grid = self._get_param_grid()
                grid_search = GridSearchCV(
                    model, grid, cv=5, scoring='r2', n_jobs=-1, verbose=1
                )
                grid_search.fit(X_train, y_train)

                self.best_model = grid_search.best_estimator_
                self.best_params = grid_search.best_params_
                logger.info(f"Best params from GridSearch: {self.best_params}")

                #Log best params to MLflow
                mlflow.log_params(self.best_params)
            else:
                model = self._get_model(params)
                model.fit(X_train, y_train)
                self.best_model = model
                self.best_params = params

            #Make predictions
            y_pred = self.best_model.predict(X_test)

            #Calculate metices
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            self.metrics = {
                'r2': r2,
                'mae': mae,
                'rmse': rmse
            }

            #Log model to MLflow
            mlflow.sklearn.log_model(
                sk_model=self.best_model,
                name="ev_model",
                registered_model_name=f"EV_Price_Predictor_{self.model_type.upper()}",
                skops_trusted_types=None
            )

            logger.info(f"Training complete. R2: {r2:.4f}, MAE: ${mae:.2f}")
            logger.info(f"Model log to MLflow with run_id: {self.run_id}")

            return self.metrics

    def save_model(self, filepath: str) -> None:
        if self.best_model is None:
            raise ValueError("No model trained. Call train() first.")
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        #Save model
        joblib.dump(self.best_model, filepath)
        logger.info(f"Model saved to {filepath}")

        #Save scaler if used
        if self.scaler is not None:
            scaler_path = filepath.parent / "scaler.pkl"
            joblib.dump(self.scaler, scaler_path)
            logger.info(f"Scaler saved to {scaler_path}")

    def get_model_info(self) -> Dict:
        if self.best_model is None:
            return {"error": "No model trained yet"}
        return {
            "model_type": self.model_type,
            "run_id": self.run_id,
            "best_params": self.best_params,
            "metrics": self.metrics,
            "experiment_name": self.experiment_name
        }

#Helper functions
def run_training_pipeline(
    data_path: str,
    model_type: str = "xgboost",
    experiment_name: str = "EV_Price_Prediction",
    use_grid_search: bool = False,
    output_dir: str = "models/artifacts"
) -> Dict:
    from src.data.pipeline import DataPipeline

    #Load and process data
    pipeline = DataPipeline(data_path)
    pipeline.load_data()
    pipeline.clean_data()
    pipeline.engineer_features()

    #Intialize trainer
    trainer = ModelTrainer(
        experiment_name=experiment_name,
        model_type=model_type
    )

    #Prepare data
    X_train, X_test, y_train, y_test, features = trainer.prepare_data(
        pipeline.df,
        scale_features=True
    )

    #Train model
    metrics = trainer.train(
        X_train, y_train,
        X_test, y_test,
        use_grid_search=use_grid_search
    )

    #Save model locally
    model_path = Path(output_dir) / f"{model_type}_model.pkl"
    trainer.save_model(str(model_path))

    print(f"Training complete for {model_type.upper()}!")
    print(f" R2: {metrics['r2']:.4f}")
    print(f" MAE: ${metrics['mae']:.2f}")
    print(f" RMSE: ${metrics['rmse']:.2f}")
    print(f" Model saved to: {model_path}")
    print(f" MLflow Run ID: {trainer.run_id}")
    print(f" View in MLflow: mlflow ui")

    return trainer.get_model_info()

#Direct Execution
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.models.trainer <path_to_raw_csv> [model_type]")
        print("Example: python -m src.models.trainer data/raw/electric_vehicles_dataset.csv xgboost")
        sys.exit(1)

    data_path = sys.argv[1]
    model_type = sys.argv[2] if len(sys.argv) > 2 else "xgboost"

    run_training_pipeline(data_path, model_type=model_type, use_grid_search=False)