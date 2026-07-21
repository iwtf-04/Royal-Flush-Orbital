from pathlib import Path
import re
import pandas as pd


DATASET_PATH = Path(__file__).resolve().parent / "data" / "car_listings_cleaned.csv"


def extract_model(name: str, brand: str) -> str:
    """Create a simple model label from the vehicle name.

    This is a heuristic step, not a perfect NLP parser. It removes the brand,
    strips common product descriptors, and keeps the remaining model phrase.
    """
    if pd.isna(name):
        return "unknown"

    text = str(name).strip()
    brand_name = "" if pd.isna(brand) else str(brand).strip()

    if brand_name:
        text = re.sub(rf"^{re.escape(brand_name)}\s*", "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s*\(.*?\)", "", text)
    text = re.sub(r"\b\d+(?:\.\d+)?[A-Za-z]?\b", "", text)
    text = re.sub(
        r"\b(?:coe|bluehdi|eat6|panoramic|roof|sunroof|hybrid|diesel|petrol|mild|puretech|automatic|manual|a|m|x|s|g)\b",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"\s+", " ", text).strip()
    return text.title() if text else "unknown"


class VehiclePricePreprocessor:
    """Reusable preprocessing pipeline for vehicle price data."""

    def __init__(self) -> None:
        self.fill_values_: dict[str, float] = {}
        self.feature_columns_: list[str] | None = None
        self.reference_date_ = pd.Timestamp("today").normalize()

    def _prepare_dataframe(self, df: pd.DataFrame, drop_missing_price: bool = True) -> pd.DataFrame:
        prepared = df.copy()

        if "listing_url" in prepared.columns:
            prepared = prepared.drop(columns=["listing_url"])

        if "price" in prepared.columns:
            prepared["price"] = pd.to_numeric(prepared["price"], errors="coerce")
            if drop_missing_price:
                prepared = prepared.dropna(subset=["price"]).copy()

        prepared["depreciation"] = pd.to_numeric(prepared["depreciation"], errors="coerce")
        if "depreciation" not in self.fill_values_:
            self.fill_values_["depreciation"] = prepared["depreciation"].median()
        prepared["depreciation"] = prepared["depreciation"].fillna(self.fill_values_["depreciation"])

        prepared["mileage"] = (
            prepared["mileage"]
            .astype(str)
            .str.replace(r"[^0-9]", "", regex=True)
            .replace("", pd.NA)
        )
        prepared["mileage"] = pd.to_numeric(prepared["mileage"], errors="coerce")
        if "mileage" not in self.fill_values_:
            self.fill_values_["mileage"] = prepared["mileage"].median()
        prepared["mileage"] = prepared["mileage"].fillna(self.fill_values_["mileage"]).astype(int)

        prepared["owners"] = prepared["owners"].astype(str).str.extract(r"(\d+)", expand=False).astype(float)
        if "owners" not in self.fill_values_:
            self.fill_values_["owners"] = prepared["owners"].median()
        prepared["owners"] = prepared["owners"].fillna(self.fill_values_["owners"]).astype(int)

        prepared["registration_date"] = pd.to_datetime(prepared["registration_date"], errors="coerce")
        prepared["vehicle_age"] = ((self.reference_date_ - prepared["registration_date"]).dt.days / 365.25).round(2)
        if "vehicle_age" not in self.fill_values_:
            self.fill_values_["vehicle_age"] = prepared["vehicle_age"].median()
        prepared["vehicle_age"] = prepared["vehicle_age"].fillna(self.fill_values_["vehicle_age"])
        prepared = prepared.drop(columns=["registration_date"])

        prepared["model"] = prepared.apply(lambda row: extract_model(row["name"], row["brand"]), axis=1)
        prepared["model"] = prepared["model"].fillna("unknown")
        prepared["name"] = prepared["name"].fillna("unknown")

        prepared["brand"] = prepared["brand"].fillna("unknown").astype(str).str.strip().str.lower()
        prepared["model"] = prepared["model"].fillna("unknown").astype(str).str.strip().str.title()
        return prepared

    def fit(self, df: pd.DataFrame, drop_duplicates: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
        training_df = df.copy()
        if drop_duplicates:
            training_df = training_df.drop_duplicates()

        cleaned_df = self._prepare_dataframe(training_df, drop_missing_price=True)
        cleaned_df = cleaned_df.dropna(subset=["price"]).copy()

        feature_frame = cleaned_df[["depreciation", "vehicle_age", "mileage", "owners", "brand", "model"]].copy()
        X = pd.get_dummies(feature_frame, columns=["brand", "model"], drop_first=True)
        self.feature_columns_ = X.columns.tolist()

        y = cleaned_df["price"].astype(float)
        return cleaned_df, X, y

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.feature_columns_ is None:
            raise ValueError("The preprocessor must be fitted before transforming new data.")

        cleaned_df = self._prepare_dataframe(df, drop_missing_price=False)
        feature_frame = cleaned_df[["depreciation", "vehicle_age", "mileage", "owners", "brand", "model"]].copy()
        X = pd.get_dummies(feature_frame, columns=["brand", "model"], drop_first=True)
        return X.reindex(columns=self.feature_columns_, fill_value=0)

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
        return self.fit(df)


def preprocess_dataset(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, VehiclePricePreprocessor]:
    print("Step 1: Loading the CSV file")
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    preprocessor = VehiclePricePreprocessor()
    cleaned_df, X, y = preprocessor.fit_transform(df)

    print("\nPreprocessing complete.")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print("\nPreview of the prepared features:")
    print(X.head())

    return cleaned_df, X, y, preprocessor


def main() -> None:
    processed_df, X, y, _ = preprocess_dataset(DATASET_PATH)
    print("\nFinal cleaned dataframe preview:")
    print(processed_df.head())


if __name__ == "__main__":
    main()
