from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date

from auth import (
    LoginRequest,
    LoginResponse,
    create_session_token,
    get_all_users,
    create_user,
    delete_user,
    get_user_by_username,
    get_username_from_token,
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
from inventory import get_vehicle_by_id, calculate_risk_score, determine_risk_level, determine_recommendation
from valuation import (
    calculate_parf_rebate,
    calculate_parf_rebate_by_scheme,
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


class SimulationRequest(BaseModel):
    coePercent: float  # e.g., -20 to +20
    parfScheme: str  # "pre" for pre-Budget2026, "post" for post-Budget2026
    depreciationRate: float  # decimal fraction e.g., 0.05 for 5%


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str


ALLOWED_USER_ROLES = ['admin', 'dealer', 'inventory manager', 'frontline staff']


def get_current_user(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing authorization token')
    token = authorization.split(' ', 1)[1]
    username = get_username_from_token(token)
    if not username:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid user account')
    return user


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


@app.get("/api/users")
async def list_users(authorization: Optional[str] = Header(None)):
    current_user = get_current_user(authorization)
    if current_user["role"] not in ("admin", "dealer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to manage users")
    return {"users": get_all_users()}


@app.post("/api/users")
async def create_user_account(request: UserCreateRequest, authorization: Optional[str] = Header(None)):
    current_user = get_current_user(authorization)
    if current_user["role"] not in ("admin", "dealer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to manage users")

    username = request.username.strip()
    role = request.role.strip().lower()
    if not username or not request.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if role not in ALLOWED_USER_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(ALLOWED_USER_ROLES)}")
    if get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already exists")

    user = create_user(username, request.password, role)
    return {"success": True, "user": user}


@app.delete("/api/users/{user_id}")
async def remove_user_account(user_id: int, authorization: Optional[str] = Header(None)):
    current_user = get_current_user(authorization)
    if current_user["role"] not in ("admin", "dealer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to manage users")
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove your own user account")

    deleted = delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "deleted_id": user_id}


@app.post("/api/inventory/{vehicle_id}/simulate")
async def simulate_vehicle_scenario(vehicle_id: int, request: SimulationRequest, authorization: Optional[str] = Header(None)):
    # Simple auth: expect Bearer token in Authorization header
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
    # Validate token and role
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    username = None
    from auth import get_username_from_token, get_user_by_username

    username = get_username_from_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_username(username)
    if not user or user.get("role") not in ("dealer", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to run simulations")

    vehicle = get_vehicle_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Apply simulation
    current_value = float(vehicle.get("current_market_value") or vehicle.get("estimated_value") or 0)
    purchase_price = float(vehicle.get("purchase_price") or 0)
    arf = float(vehicle.get("arf") or 0)
    coe = float(vehicle.get("coe") or vehicle.get("current_coe") or 0)

    coe_multiplier = 1.0 + (request.coePercent / 100.0)
    depreciation_rate = float(request.depreciationRate)

    # Determine simulated PARF rebate from chosen policy scheme
    if request.parfScheme not in ("pre", "post"):
        raise HTTPException(status_code=400, detail="parfScheme must be 'pre' or 'post'.")

    vehicle_registration_date = vehicle.get("registration_date")
    age_years = 0.0
    if vehicle_registration_date:
        try:
            registration_date = date.fromisoformat(vehicle_registration_date)
            age_years = round(max(0.0, (date.today() - registration_date).days / 365.25), 2)
        except ValueError:
            age_years = 0.0

    parf_rebate = calculate_parf_rebate_by_scheme(age_years, arf, request.parfScheme)
    simulated_base = arf + coe + parf_rebate
    simulated_value = simulated_base * coe_multiplier
    depreciation_loss = simulated_value * depreciation_rate
    simulated_value = max(0.0, simulated_value - depreciation_loss)

    # For simplicity assume simulated selling price equals simulated value
    simulated_selling_price = simulated_value
    simulated_profit = simulated_selling_price - purchase_price
    simulated_margin = (simulated_profit / simulated_selling_price * 100.0) if simulated_selling_price > 0 else 0.0

    # Risk and recommendation using existing helpers
    risk_score = calculate_risk_score(int(vehicle.get("days_in_inventory") or 0), depreciation_rate, (simulated_margin / 100.0))
    risk_level = determine_risk_level(risk_score)
    recommendation = determine_recommendation(int(vehicle.get("days_in_inventory") or 0), depreciation_rate, (simulated_margin / 100.0))

    return {
        "vehicle": vehicle,
        "current": {
            "selling_price": current_value,
            "profit": (current_value - purchase_price),
            "margin": round(( (current_value - purchase_price) / current_value * 100.0) if current_value > 0 else 0.0, 2),
        },
        "simulated": {
            "selling_price": round(simulated_selling_price, 2),
            "profit": round(simulated_profit, 2),
            "margin_percent": round(simulated_margin, 2),
            "risk_level": risk_level,
            "risk_score": round(risk_score, 3),
            "recommendation": recommendation.get("recommendation"),
            "recommendation_reason": recommendation.get("recommendation_reason"),
        },
        "inputs": {
            "coePercent": request.coePercent,
            "parfScheme": request.parfScheme,
            "depreciationRate": request.depreciationRate,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
