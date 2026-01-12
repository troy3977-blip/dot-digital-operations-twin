from typing import Dict
from .kpis import KPIResult
from .operating_models import (
    OperatingModelConfig,
    OperatingModelType,
    get_default_operating_models,
)

def _effective_capacity(model: OperatingModelConfig) -> float:
    """
    Toy capacity model:
    - staffing_level is primary capacity driver
    - vendor_support adds burst capacity
    - digital_penetration offloads some load
    """
    base = 1.0  # normalized capacity
    staff_factor = 0.7 * model.staffing_level
    vendor_factor = 0.3 * model.vendor_support
    digital_factor = 0.2 * model.digital_penetration  # reduces strain

    return base + staff_factor + vendor_factor + digital_factor

def _effective_demand(shock_intensity: float) -> float:
    """
    Toy demand model:
    - 1.0 is a 'normal' year
    - shock_intensity increases demand up to +100%
      (you can tune this multiplier)
    """
    return 1.0 * (1.0 + 1.0 * shock_intensity)

def _approximate_utilization(demand: float, capacity: float) -> float:
    """
    Utilization = demand / capacity, but clamp it to a reasonable range.
    """
    if capacity <= 0:
        return 2.0  # totally overloaded
    return max(0.2, min(2.0, demand / capacity))

def _map_to_kpis(
    model: OperatingModelConfig,
    utilization: float,
    shock_intensity: float,
) -> KPIResult:
    """
    Map utilization and model settings into Cost / Access / Resilience / ROI.

    Intuition:
    - Higher staffing/vendor/digital -> higher cost, better access/resilience
    - Higher utilization (closer to or >1) -> worse access/resilience
    - Higher shock_intensity -> stresses system, slightly raises cost
    - risk_tolerance shifts ROI perception
    """

    # --- Cost model ---
    base_cost = 100.0
    staffing_cost = 60.0 * model.staffing_level
    vendor_cost = 25.0 * model.vendor_support
    digital_cost = 15.0 * model.digital_penetration
    shock_cost = 10.0 * shock_intensity  # overtime, surge staffing, etc.

    total_cost = base_cost + staffing_cost + vendor_cost + digital_cost + shock_cost

    # --- Access model (higher utilization hurts access) ---
    # utilization ~0.7–0.9 is sweet spot, >1 is bad
    if utilization <= 0.9:
        access_penalty = 10.0 * (0.9 - utilization)  # slight penalty if under-used
    else:
        access_penalty = 35.0 * (utilization - 0.9)  # heavier penalty if overloaded

    access_base = 80.0
    access_from_digital = 10.0 * model.digital_penetration
    access = access_base + access_from_digital - access_penalty - 15.0 * shock_intensity

    # --- Resilience model (headroom above 1.0 utilization) ---
    # If utilization << 1, resilience high; if >1, resilience low.
    if utilization < 1.0:
        resilience = 70.0 + 40.0 * (1.0 - utilization)
    else:
        resilience = 70.0 - 60.0 * (utilization - 1.0)

    # vendor support contributes to resilience
    resilience += 10.0 * model.vendor_support
    resilience -= 20.0 * shock_intensity  # big shocks erode resilience

    # --- ROI model ---
    # Think of ROI as "is the extra spend justified given access & resilience?"
    # A simple proxy: combine access & resilience, subtract cost and risk-tolerance.
    value_signal = 0.4 * access + 0.4 * resilience
    cost_signal = 0.2 * (total_cost - 100.0)  # incremental cost hurts ROI

    roi = 70.0 + 0.4 * value_signal - 0.3 * cost_signal - 15.0 * model.risk_tolerance

    # clamp 0–100
    def clamp(x): return max(0, min(100, x))

    return KPIResult(
        total_cost=round(total_cost, 1),
        access_score=round(clamp(access), 1),
        resilience_margin=round(clamp(resilience), 1),
        roi_score=round(clamp(roi), 1),
    )

def run_single_scenario(
    operating_model: OperatingModelConfig,
    shock_intensity: float,  # 0–1
) -> KPIResult:
    """
    Main entry point used by the UI.

    1. Compute effective capacity for the model
    2. Compute effective demand given the shock
    3. Derive utilization
    4. Map to KPIs
    """
    demand = _effective_demand(shock_intensity)
    capacity = _effective_capacity(operating_model)
    utilization = _approximate_utilization(demand, capacity)
    return _map_to_kpis(operating_model, utilization, shock_intensity)

def run_all_operating_models(shock_intensity: float) -> Dict[OperatingModelType, KPIResult]:
    models = get_default_operating_models()
    return {
        om_type: run_single_scenario(cfg, shock_intensity)
        for om_type, cfg in models.items()
    }
