import os
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd

try:
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "joblib", "scikit-learn"])
    from sklearn.ensemble import RandomForestRegressor

ML_DIR = Path(__file__).resolve().parent
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

from preprocess import DATASET_PATH, VehiclePricePreprocessor, preprocess_dataset


MODEL_PATH = Path(__file__).resolve().parent / "best_model.joblib"
PREPROCESSOR_PATH = Path(__file__).resolve().parent / "preprocessor.joblib"
PIPELINE_PATH = Path(__file__).resolve().parent / "pipeline.joblib"


def train_fallback_model() -> tuple[object, VehiclePricePreprocessor]:
    """Train a Random Forest regressor from the dataset when saved artifacts are unavailable."""
    _, X, y, preprocessor = preprocess_dataset(DATASET_PATH)
    model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    return model, preprocessor


def load_model_and_preprocessor() -> tuple[object, VehiclePricePreprocessor]:
    """Load the trained model and the fitted preprocessing object."""
    if PIPELINE_PATH.exists():
        pipeline = joblib.load(PIPELINE_PATH)
        return pipeline["model"], pipeline["preprocessor"]

    if MODEL_PATH.exists() and PREPROCESSOR_PATH.exists():
        model = joblib.load(MODEL_PATH)
        preprocessor = joblib.load(PREPROCESSOR_PATH)
        return model, preprocessor

    return train_fallback_model()


def predict_price(
    brand: str,
    name: str,
    registration_date: str,
    mileage: str | int | float,
    owners: str | int | float,
    depreciation: str | int | float,
) -> float:
    """Prepare a single vehicle record and return its predicted selling price."""
    model, preprocessor = load_model_and_preprocessor()

    input_df = pd.DataFrame(
        [
            {
                "brand": brand,
                "name": name,
                "registration_date": registration_date,
                "mileage": mileage,
                "owners": owners,
                "depreciation": depreciation,
            }
        ]
    )

    features = preprocessor.transform(input_df)
    prediction = model.predict(features)[0]
    return float(prediction)


if __name__ == "__main__":
    example_price = predict_price(
        brand="toyota",
        name="Toyota Corolla Altis 1.6A",
        registration_date="2019-07-19",
        mileage=12000,
        owners=2,
        depreciation=13220,
    )
    print(f"Predicted price: {example_price:.2f}")
