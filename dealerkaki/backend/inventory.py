from datetime import date, datetime
import uuid
from typing import List, Dict, Any
from database import get_conn


def calculate_inventory_age_factor(days: int) -> float:
    if days <= 30:
        return 0.1
    if days <= 60:
        return 0.3
    if days <= 90:
        return 0.6
    return 1.0


def calculate_depreciation_factor(rate: float) -> float:
    if rate <= 0.05:
        return 0.1
    if rate <= 0.1:
        return 0.4
    return 1.0


def calculate_margin_factor(margin: float) -> float:
    if margin >= 0.15:
        return 0.1
    if margin >= 0.08:
        return 0.4
    return 1.0


def calculate_risk_score(days: int, depreciation_rate: float, profit_margin: float) -> float:
    return (
        0.4 * calculate_inventory_age_factor(days)
        + 0.3 * calculate_depreciation_factor(depreciation_rate)
        + 0.3 * calculate_margin_factor(1 - profit_margin)
    )


def determine_risk_level(score: float) -> str:
    if score <= 0.35:
        return "LOW"
    if score <= 0.65:
        return "MEDIUM"
    return "HIGH"


def determine_recommendation(days: int, depreciation_rate: float, profit_margin: float) -> Dict[str, str]:
    if days > 60 and depreciation_rate > 0.1:
        return {
            "recommendation": "SELL SOON",
            "recommendation_reason": "Days in inventory and depreciation are both high.",
        }
    if days < 30 and profit_margin >= 0.12:
        return {
            "recommendation": "HOLD INVENTORY",
            "recommendation_reason": "Recent acquisition with healthy profit margin.",
        }
    if profit_margin < 0.05 or days > 90:
        return {
            "recommendation": "SELL SOON",
            "recommendation_reason": "Margin is low or vehicle has been in stock too long.",
        }
    return {
        "recommendation": "MONITOR",
        "recommendation_reason": "Continue tracking value and margin before moving the vehicle.",
    }


def _normalize_vehicle(row: Dict[str, Any]) -> Dict[str, Any]:
    vehicle = dict(row)
    current_market_value = vehicle.get("current_market_value") or vehicle.get("estimated_value") or 0
    purchase_price = vehicle.get("purchase_price") or (vehicle.get("arf") or 0) + (vehicle.get("coe") or 0)
    profit_margin = vehicle.get("profit_margin")
    if profit_margin is None or profit_margin == 0:
        profit_margin = ((current_market_value - purchase_price) / purchase_price) if purchase_price else 0
    profit_margin = round(profit_margin, 4)
    days_in_inventory = int(vehicle.get("days_in_inventory") or 0)
    depreciation_rate = float(vehicle.get("depreciation_rate") or 0)
    risk_level = vehicle.get("risk_level")
    if not risk_level:
        risk_score = calculate_risk_score(days_in_inventory, depreciation_rate, profit_margin)
        risk_level = determine_risk_level(risk_score)
    else:
        risk_score = calculate_risk_score(days_in_inventory, depreciation_rate, profit_margin)

    recommendation_data = determine_recommendation(days_in_inventory, depreciation_rate, profit_margin)

    vehicle_age = date.today().year - int(vehicle.get("year") or date.today().year)
    sold_price = float(vehicle.get("sold_price") or 0)
    profit_amount = sold_price - purchase_price if sold_price > 0 else current_market_value - purchase_price
    return {
        "id": vehicle["id"],
        "vehicle_id": vehicle.get("license_plate") or vehicle.get("vin") or "",
        "vin": vehicle.get("vin") or "",
        "license_plate": vehicle.get("license_plate") or "",
        "make": vehicle.get("make") or "",
        "model": vehicle.get("model") or "",
        "year": int(vehicle.get("year") or 0),
        "age": vehicle_age,
        "mileage": int(vehicle.get("mileage") or 0),
        "purchase_price": float(purchase_price),
        "arf": float(vehicle.get("arf") or 0),
        "registration_date": vehicle.get("registration_date") or "",
        "current_market_value": float(current_market_value),
        "recommended_intake_price": float(vehicle.get("recommended_intake_price") or max(current_market_value * 0.92, purchase_price * 0.95)),
        "target_selling_price": float(vehicle.get("target_selling_price") or max(current_market_value * 1.08, purchase_price * 1.05)),
        "date_acquired": vehicle.get("date_acquired") or vehicle.get("entry_date") or "",
        "entry_date": vehicle.get("entry_date") or "",
        "coe_at_purchase": float(vehicle.get("coe_at_purchase") or 0),
        "current_coe": float(vehicle.get("current_coe") or vehicle.get("coe") or 0),
        "coe": float(vehicle.get("coe") or 0),
        "estimated_value": float(vehicle.get("estimated_value") or current_market_value),
        "depreciation_rate": depreciation_rate,
        "profit_margin": profit_margin,
        "profit_amount": profit_amount,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "recommendation": vehicle.get("recommendation") or recommendation_data["recommendation"],
        "recommendation_reason": vehicle.get("recommendation_reason") or recommendation_data["recommendation_reason"],
        "sold_price": sold_price,
        "sold_date": vehicle.get("sold_date") or "",
        "vehicle_type": vehicle.get("vehicle_type") or "",
        "seat_count": int(vehicle.get("seat_count") or 0),
        "days_in_inventory": days_in_inventory,
        "status": (vehicle.get("status") or "AVAILABLE").upper(),
    }


def get_all_vehicles() -> List[Dict[str, Any]]:
    """Fetch all vehicles in inventory."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM vehicles
            ORDER BY days_in_inventory DESC
            """
        ).fetchall()
        return [_normalize_vehicle(dict(row)) for row in rows]


def get_vehicle_by_id(vehicle_id: int) -> Dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM vehicles WHERE id = ?",
            (vehicle_id,),
        ).fetchone()
        return _normalize_vehicle(dict(row)) if row else None


def create_inventory_vehicle(data: Dict[str, Any]) -> Dict[str, Any]:
    entry_date = data.get("entry_date") or date.today().isoformat()
    date_acquired = data.get("date_acquired") or entry_date
    acquired_date = date.fromisoformat(date_acquired)
    days_in_inventory = max(0, (date.today() - acquired_date).days)
    purchase_price = float(data.get("agreed_purchase_cost") or data.get("purchase_price") or 0)
    current_market_value = float(data.get("estimated_market_value") or 0)
    profit_margin = round((current_market_value - purchase_price) / purchase_price, 4) if purchase_price else 0.0
    risk_score = calculate_risk_score(days_in_inventory, float(data.get("depreciation_rate") or 0), profit_margin)
    risk_level = determine_risk_level(risk_score)
    recommendation_data = determine_recommendation(days_in_inventory, float(data.get("depreciation_rate") or 0), profit_margin)
    vin_value = data.get("vin") or f"GEN{uuid.uuid4().hex[:13].upper()}"
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO vehicles (
                vin,
                license_plate,
                make,
                model,
                year,
                mileage,
                purchase_price,
                arf,
                coe,
                coe_at_purchase,
                current_coe,
                registration_date,
                date_acquired,
                entry_date,
                estimated_value,
                current_market_value,
                recommended_intake_price,
                target_selling_price,
                depreciation_rate,
                profit_margin,
                risk_level,
                recommendation,
                recommendation_reason,
                sold_price,
                sold_date,
                vehicle_type,
                seat_count,
                days_in_inventory,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vin_value,
                data.get("license_plate") or "",
                data.get("make") or "",
                data.get("model") or "",
                int(data.get("year") or 0),
                int(data.get("mileage") or 0),
                purchase_price,
                float(data.get("arf") or 0),
                float(data.get("coe") or 0),
                float(data.get("current_coe") or data.get("coe") or 0),
                float(data.get("current_coe") or data.get("coe") or 0),
                data.get("registration_date") or "",
                date_acquired,
                entry_date,
                float(data.get("estimated_value") or current_market_value),
                current_market_value,
                float(data.get("recommended_intake_price") or current_market_value),
                float(data.get("target_selling_price") or data.get("recommended_intake_price") or current_market_value),
                float(data.get("depreciation_rate") or 0),
                profit_margin,
                risk_level,
                recommendation_data["recommendation"],
                recommendation_data["recommendation_reason"],
                0,
                "",
                data.get("vehicle_type") or "",
                int(data.get("seat_count") or 0),
                days_in_inventory,
                "AVAILABLE",
            ),
        )
        vehicle_id = cursor.lastrowid
    return get_vehicle_by_id(vehicle_id)


def sell_inventory_vehicle(vehicle_id: int, sold_price: float, sold_date: str | None = None) -> Dict[str, Any] | None:
    sold_date = sold_date or date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE vehicles
            SET status = 'SOLD', sold_price = ?, sold_date = ?
            WHERE id = ?
            """,
            (sold_price, sold_date, vehicle_id),
        )
    return get_vehicle_by_id(vehicle_id)


def delete_inventory_vehicle(vehicle_id: int) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM vehicles WHERE id = ?",
            (vehicle_id,),
        )
        return cursor.rowcount > 0


def get_vehicles_by_status(status: str) -> List[Dict[str, Any]]:
    """Fetch vehicles by status (AVAILABLE, RESERVED, SOLD)."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM vehicles
            WHERE UPPER(status) = ?
            ORDER BY days_in_inventory DESC
            """,
            (status.upper(),),
        ).fetchall()
        return [_normalize_vehicle(dict(row)) for row in rows]


def get_vehicles_by_risk_level(risk_level: str) -> List[Dict[str, Any]]:
    """Fetch vehicles by risk level (LOW, MEDIUM, HIGH)."""
    all_vehicles = get_all_vehicles()
    return [vehicle for vehicle in all_vehicles if vehicle["risk_level"] == risk_level.upper()]


def get_inventory_summary() -> Dict[str, Any]:
    """Get inventory summary statistics."""
    vehicles = get_all_vehicles()
    total_value = sum(vehicle["current_market_value"] for vehicle in vehicles)
    high_risk_count = sum(1 for vehicle in vehicles if vehicle["risk_level"] == "HIGH")
    average_days = sum(vehicle["days_in_inventory"] for vehicle in vehicles) / max(len(vehicles), 1)

    return {
        "total_vehicles": len(vehicles),
        "high_risk_count": high_risk_count,
        "total_inventory_value": total_value,
        "average_days_in_inventory": average_days,
    }
