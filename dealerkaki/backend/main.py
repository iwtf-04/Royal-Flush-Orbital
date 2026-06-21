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
from inventory import (
    create_inventory_vehicle,
    delete_inventory_vehicle,
    get_all_vehicles,
    get_inventory_summary,
    get_vehicles_by_risk_level,
    sell_inventory_vehicle,
)
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


class InventoryAddRequest(BaseModel):
    vin: Optional[str] = ""
    licensePlate: Optional[str] = ""
    make: str
    model: str
    year: int
    mileage: int
    arf: float
    coe: float
    currentCoe: Optional[float] = None
    registrationDate: str
    agreedPurchaseCost: float
    estimatedMarketValue: float
    recommendedIntakePrice: float
    targetSellingPrice: Optional[float] = None
    depreciationRate: Optional[float] = None
    dateAcquired: Optional[str] = None
    vehicleType: Optional[str] = ""
    seatCount: Optional[int] = 5


class InventorySaleRequest(BaseModel):
    soldPrice: float
    soldDate: Optional[str] = None


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


@app.get("/api/inventory")
async def get_inventory():
    """Fetch all vehicles in inventory."""
    vehicles = get_all_vehicles()
    summary = get_inventory_summary()
    return {
        "vehicles": vehicles,
        "summary": summary,
    }


@app.get("/api/inventory/summary")
async def get_summary():
    """Fetch inventory summary statistics."""
    summary = get_inventory_summary()
    return summary


@app.get("/api/inventory/high-risk")
async def get_high_risk():
    """Fetch high-risk vehicles."""
    vehicles = get_vehicles_by_risk_level("HIGH")
    return {
        "vehicles": vehicles,
        "count": len(vehicles),
    }


@app.post("/api/inventory/add")
async def add_inventory_item(request: InventoryAddRequest):
    try:
        date.fromisoformat(request.registrationDate)
        if request.dateAcquired:
            date.fromisoformat(request.dateAcquired)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    vehicle = create_inventory_vehicle({
        "vin": request.vin,
        "license_plate": request.licensePlate,
        "make": request.make,
        "model": request.model,
        "year": request.year,
        "mileage": request.mileage,
        "arf": request.arf,
        "coe": request.coe,
        "current_coe": request.currentCoe,
        "registration_date": request.registrationDate,
        "agreed_purchase_cost": request.agreedPurchaseCost,
        "estimated_market_value": request.estimatedMarketValue,
        "recommended_intake_price": request.recommendedIntakePrice,
        "target_selling_price": request.targetSellingPrice or request.recommendedIntakePrice,
        "depreciation_rate": request.depreciationRate or 0,
        "date_acquired": request.dateAcquired,
        "vehicle_type": request.vehicleType,
        "seat_count": request.seatCount,
    })
    return {"success": True, "vehicle": vehicle}


@app.post("/api/inventory/{vehicle_id}/sell")
async def sell_inventory_item(vehicle_id: int, request: InventorySaleRequest):
    if request.soldPrice <= 0:
        raise HTTPException(status_code=400, detail="Final sold price must be greater than zero.")
    try:
        if request.soldDate:
            date.fromisoformat(request.soldDate)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    vehicle = sell_inventory_vehicle(vehicle_id, request.soldPrice, request.soldDate)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return {"success": True, "vehicle": vehicle}


@app.delete("/api/inventory/{vehicle_id}")
async def delete_inventory_item(vehicle_id: int):
    deleted = delete_inventory_vehicle(vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return {"success": True, "deleted_id": vehicle_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
