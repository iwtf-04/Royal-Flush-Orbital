from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date

from auth import (
    LoginRequest,
    LoginResponse,
    create_session_token,
    get_user_by_username,
    verify_user_credentials,
)
from database import init_db
from valuation import (
    calculate_parf_rebate,
    calculate_base_depreciation,
    estimate_market_price,
    recommend_intake_price,
    get_vehicle_valuation,
)

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    init_db()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
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


@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = get_user_by_username(request.username)
    if user is None or not verify_user_credentials(request.username, request.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_session_token(request.username)
    return LoginResponse(
        success=True,
        message="Login successful",
        token=token,
        username=user["username"],
        role=user["role"],
    )


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
