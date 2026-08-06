import pytest
import pandas as pd
from pathlib import Path
from src.data.pipeline import DataPipeline

def test_pipeline_full_flow(tmp_path):
    test_data = pd.DataFrame({
        'Manufacturer': ['Tesla', 'Nissan', 'BMW'],
        'Model': ['Model 3', 'Leaf', 'X5'],
        'Year': [2024, 2018, 2022],
        'Battery_Capacity_kWh': [75.0, 40.0, 60.0],
        'Range_km': [500, 200, 450],
        'Charge_Time_hr': [8.0, 6.0, 7.5],
        'Price_USD': [80000, 30000, 65000],
        'Autonomous_Level': [3.0, 0.0, 2.0],
        'Safety_Rating': [5.0, 4.0, 4.5],
        'Warranty_Years': [4, 3, 3]
    })

    #save test csv
    test_csv = tmp_path / "test_data.csv"
    test_data.to_csv(test_csv, index=False)

    #Initialize pipline
    pipeline = DataPipeline(str(test_csv), current_year=2026)

    #Run pipeline
    df = pipeline.load_data()
    assert df is not None

    df = pipeline.load_data()
    assert df.isnull().sum().sum() == 0

    df = pipeline.engineer_features()
    assert 'Vehicle_Age' in df.columns
    assert 'Efficiency_Score' in df.columns
    assert 'Brand_Enc' in df.columns
    assert 'Model_Enc' in df.columns

    #Test split
    X_train, X_test, y_train, y_test = pipeline.get_train_test_split()
    assert len(X_train) > 0
    assert len(X_test) > 0
    assert len(y_train) > 0
    assert len(y_test) > 0

    #Test encoding retrievel
    brand_map, model_map, global_avg = pipeline.get_encodings()
    assert 'Tesla' in brand_map
    assert 'Model 3' in model_map
    assert global_avg > 0

    #Test saving processed data
    processed_path = tmp_path / "processed.csv"
    pipeline.save_processed_data(str(processed_path))
    assert processed_path.exists()

def test_clean_handles_missing():
    import tempfile

    data = pd.DataFrame({
        'Manufacturer': ['Tesla'],
        'Model': ['Model 3'],
        'Year': [2024],
        'Battery_Capacity_kWh': [75.0],
        'Range_km': [500],
        'Charge_Time_hr': [8.0],
        'Autonomous_Level': [None],
        'Safety_Rating': [None],
        'Warranty_Years': [4]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = f.name

    pipeline = DataPipeline(csv_path)
    df = pipeline.load_data()

    #Check that NaN is filled
    assert df['Autonomous_Level'].iloc[0] == 0

    assert df is not None
