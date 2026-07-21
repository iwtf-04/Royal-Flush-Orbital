import sys
from pathlib import Path

import joblib
import pandas as pd

ML_DIR = Path(__file__).resolve().parent / "ml"
if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))

from preprocess import VehiclePricePreprocessor


MODEL_PATH = Path(__file__).resolve().parent / "ml" / "best_model.joblib"
PREPROCESSOR_PATH = Path(__file__).resolve().parent / "ml" / "preprocessor.joblib"
PIPELINE_PATH = Path(__file__).resolve().parent / "ml" / "pipeline.joblib"


def load_model_and_preprocessor() -> tuple[object, VehiclePricePreprocessor]:
    if PIPELINE_PATH.exists():
        pipeline = joblib.load(PIPELINE_PATH)
        return pipeline["model"], pipeline["preprocessor"]

    if MODEL_PATH.exists() and PREPROCESSOR_PATH.exists():
        model = joblib.load(MODEL_PATH)
        preprocessor = joblib.load(PREPROCESSOR_PATH)
        return model, preprocessor

    raise FileNotFoundError("Prediction model files are not available")


def predict_price(
    brand: str,
    name: str,
    registration_date: str,
    mileage: int,
    owners: int,
    depreciation: float,
) -> float:
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
