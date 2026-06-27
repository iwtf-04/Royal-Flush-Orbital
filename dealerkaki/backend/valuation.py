from datetime import date

# Budget 2026 cutoff: new PARF schedule applies to cars registered on/after this date
PARF_2026_CUTOFF = date(2026, 2, 13)

# (age_upper_bound_exclusive, old_rate, new_rate)
_PARF_BRACKETS = [
    (5,  0.75, 0.30),
    (6,  0.70, 0.25),
    (7,  0.65, 0.20),
    (8,  0.60, 0.15),
    (9,  0.55, 0.10),
    (10, 0.50, 0.05),
]
_OLD_PARF_CAP = 60_000
_NEW_PARF_CAP = 30_000


def _is_pre_cutoff(registration_date: date) -> bool:
    return registration_date < PARF_2026_CUTOFF


def _calculate_age_years(registration_date: date, reference_date: date | None = None) -> float:
    if reference_date is None:
        reference_date = date.today()
    age_days = (reference_date - registration_date).days
    return round(max(0.0, age_days / 365.25), 2)


def _parf_rate(age_years: float, pre_cutoff: bool) -> float:
    """Return the applicable PARF rebate rate for a given age and scheme."""
    for upper, old_rate, new_rate in _PARF_BRACKETS:
        if age_years < upper:
            return old_rate if pre_cutoff else new_rate
    return 0.0  # >= 10 years: no PARF eligibility


def calculate_parf_rebate(age_years: float, arf: float, registration_date: date) -> float:
    """
    Calculate PARF rebate using the correct tiered bracket and cap.

    Pre-13 Feb 2026: 75%→50% of ARF, capped at $60,000.
    Post-13 Feb 2026: 30%→5% of ARF, capped at $30,000.
    """
    if age_years >= 10:
        return 0.0
    pre_cutoff = _is_pre_cutoff(registration_date)
    rate = _parf_rate(age_years, pre_cutoff)
    cap = _OLD_PARF_CAP if pre_cutoff else _NEW_PARF_CAP
    return round(min(arf * rate, cap))


def _minimum_parf_value_at_coe_end(arf: float, registration_date: date) -> float:
    """Return the minimum PARF value payable at the end of a 10-year COE life."""
    pre_cutoff = _is_pre_cutoff(registration_date)
    rate = 0.50 if pre_cutoff else 0.05
    cap = _OLD_PARF_CAP if pre_cutoff else _NEW_PARF_CAP
    return round(min(arf * rate, cap))


def calculate_base_depreciation(
    age_years: float, arf: float, coe: float, registration_date: date
) -> float:
    """
    Calculate annual depreciation based on COE life remaining.

    Depreciation = (List Price - Minimum PARF value) / remaining years of COE.
    The value of the car body is not taken into account.
    """
    remaining_years = max(0.0, 10.0 - age_years)
    if remaining_years <= 0:
        return 0.0

    list_price = arf + coe
    minimum_parf_value = _minimum_parf_value_at_coe_end(arf, registration_date)
    depreciation = (list_price - minimum_parf_value) / remaining_years
    return round(max(0.0, depreciation))


def estimate_market_price(
    age_years: float, arf: float, coe: float, registration_date: date
) -> float:
    """
    Estimate market price.

    Pre-cutoff cars command a premium in the used market: a future buyer
    inherits the old (more generous) PARF schedule, making the car
    objectively worth more than an identical post-cutoff vehicle.
    """
    parf_rebate = calculate_parf_rebate(age_years, arf, registration_date)
    depreciation = calculate_base_depreciation(age_years, arf, coe, registration_date)
    trend_adjustment = max(0.0, 1 - age_years * 0.03)
    raw_value = arf + coe + parf_rebate - depreciation

    # Old-scheme cars carry a used-market premium
    scheme_premium = 1.03 if _is_pre_cutoff(registration_date) else 1.0
    return round(raw_value * trend_adjustment * scheme_premium)


def recommend_intake_price(
    age_years: float, arf: float, coe: float, registration_date: date
) -> float:
    """
    Recommend intake price based on market price and risk premium.

    New-scheme cars carry higher depreciation risk, so the dealer discount
    is larger to protect margin.
    """
    market_price = estimate_market_price(age_years, arf, coe, registration_date)
    pre_cutoff = _is_pre_cutoff(registration_date)

    if age_years >= 7:
        risk_premium = 0.08 if pre_cutoff else 0.12
    elif age_years >= 4:
        risk_premium = 0.05 if pre_cutoff else 0.08
    else:
        risk_premium = 0.03 if pre_cutoff else 0.05

    return max(0, round(market_price * (1 - risk_premium)))


def get_vehicle_valuation(
    arf: float,
    coe: float,
    registration_date: date,
) -> dict:
    """
    Get complete vehicle valuation with all metrics.

    Args:
        arf:               Additional Registration Fee paid (SGD).
        coe:               Certificate of Entitlement value at registration (SGD).
        registration_date: Date the vehicle was first registered in Singapore.
                           Determines which PARF scheme applies.
    """
    if not isinstance(registration_date, date):
        raise ValueError("registration_date must be a datetime.date object.")
    if not all(isinstance(v, (int, float)) for v in (arf, coe)):
        raise ValueError("arf and coe must be numbers.")
    if any(v < 0 for v in (arf, coe)):
        raise ValueError("arf and coe must be non-negative.")

    age_years = _calculate_age_years(registration_date)
    pre_cutoff = _is_pre_cutoff(registration_date)

    return {
        "ageYears": age_years,
        "arf": arf,
        "coe": coe,
        "registrationDate": registration_date.isoformat(),
        "parfScheme": "pre-Budget2026" if pre_cutoff else "post-Budget2026",
        "parfCap": _OLD_PARF_CAP if pre_cutoff else _NEW_PARF_CAP,
        "estimatedParfRebate": calculate_parf_rebate(age_years, arf, registration_date),
        "depreciationValue": calculate_base_depreciation(age_years, arf, coe, registration_date),
        "estimatedMarketPrice": estimate_market_price(age_years, arf, coe, registration_date),
        "recommendedIntakePrice": recommend_intake_price(age_years, arf, coe, registration_date),
    }