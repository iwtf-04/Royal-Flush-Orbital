from datetime import date

from pydantic import BaseModel, Field


class PricePredictionRequest(BaseModel):
    brand: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    registration_date: date
    mileage: int = Field(..., ge=0)
    owners: int = Field(..., ge=0)
    depreciation: float = Field(..., ge=0)


class PricePredictionResponse(BaseModel):
    predicted_price: float
