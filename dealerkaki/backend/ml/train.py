from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

from preprocess import DATASET_PATH, preprocess_dataset


MODEL_PATH = Path(__file__).resolve().parent / "best_model.joblib"
PREPROCESSOR_PATH = Path(__file__).resolve().parent / "preprocessor.joblib"


def train_and_evaluate_models(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, dict]:
    """Split data, train multiple regression models, and compare their performance."""
    # 80/20 split gives a reasonable holdout set for measuring generalization.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree Regressor": DecisionTreeRegressor(random_state=42),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=42),
    }

    results = []
    trained_models = {}

    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        mae = mean_absolute_error(y_test, predictions)
        rmse = mean_squared_error(y_test, predictions) ** 0.5
        r2 = r2_score(y_test, predictions)

        results.append(
            {
                "model": name,
                "mae": mae,
                "rmse": rmse,
                "r2_score": r2,
            }
        )
        trained_models[name] = model

    comparison_df = pd.DataFrame(results)
    comparison_df = comparison_df.sort_values(
        by=["r2_score", "mae", "rmse"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    return comparison_df, trained_models


def display_results(results: pd.DataFrame) -> None:
    """Print the model comparison table in a readable format."""
    print("\nModel comparison results:")
    print(results.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))


def select_best_model(results: pd.DataFrame, trained_models: dict) -> tuple[str, object]:
    """Select the best model based on the highest R² and lowest error metrics."""
    best_name = results.iloc[0]["model"]
    best_model = trained_models[best_name]
    return best_name, best_model


def display_feature_importance(model: object, feature_names: list[str]) -> None:
    """Show the most important features for tree-based models."""
    if not hasattr(model, "feature_importances_"):
        print("\nThis model does not provide feature importances.")
        return

    importances = pd.Series(model.feature_importances_, index=feature_names)
    importances = importances.sort_values(ascending=False)

    print("\nTop feature importances:")
    print(importances.head(15).to_string())


def explain_best_model(best_name: str, results: pd.DataFrame) -> None:
    """Explain why the selected model performed best."""
    best_row = results.iloc[0]
    print("\nWhy this model was selected:")
    print(
        f"- {best_name} achieved the highest R² score of {best_row['r2_score']:.4f}."
    )
    print(
        f"- It also produced the lowest MAE of {best_row['mae']:.4f} and RMSE of {best_row['rmse']:.4f}."
    )
    print(
        "- This suggests it captured the relationships between vehicle age, mileage, depreciation, and categorical brand/model signals better than the simpler alternatives."
    )


def main() -> None:
    """Run preprocessing, train models, compare results, and save the best model."""
    print("Preparing the preprocessed dataset...")
    _, X, y, preprocessor = preprocess_dataset(DATASET_PATH)

    print("\nSplitting data into training and testing sets...")
    results, trained_models = train_and_evaluate_models(X, y)
    display_results(results)

    best_name, best_model = select_best_model(results, trained_models)
    explain_best_model(best_name, results)

    if best_name in {"Random Forest Regressor", "Gradient Boosting Regressor"}:
        display_feature_importance(best_model, X.columns.tolist())

    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"\nSaved best model to {MODEL_PATH}")
    print(f"Saved preprocessing object to {PREPROCESSOR_PATH}")
    print(f"Best model selected: {best_name}")


if __name__ == "__main__":
    main()
