from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date

from valuation import (
    calculate_parf_rebate,
    calculate_base_depreciation,
    estimate_market_price,
    recommend_intake_price,
    get_vehicle_valuation,
)

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValuationRequest(BaseModel):
    ageYears: float
    arf: float
    coe: float
    registrationDate: str  # ISO format: YYYY-MM-DD


class ValuationResponse(BaseModel):
    ageYears: float
    arf: float
    coe: float
    registrationDate: str
    parfScheme: str
    parfCap: float
    estimatedParfRebate: float
    depreciationValue: float
    estimatedMarketPrice: float
    recommendedIntakePrice: float


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "DealerKaki valuation API"
    }


@app.post("/api/vehicle-valuation", response_model=ValuationResponse)
async def vehicle_valuation(request: ValuationRequest):
    try:
        registration_date = date.fromisoformat(request.registrationDate)
        result = get_vehicle_valuation(
            age_years=request.ageYears,
            arf=request.arf,
            coe=request.coe,
            registration_date=registration_date
        )
        return result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
