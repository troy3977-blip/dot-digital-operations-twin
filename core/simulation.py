from typing import Dict
from .kpis import KPIResult
from .operating_models import OperatingModelConfig, OperatingModelType, get_default_operating_models

def run_single_scenario(
    operating_model: OperatingModelConfig,
    shock_intensity: float,  # 0–1
) -> KPIResult:
    """
    Placeholder mapping:
    - Higher staffing/vendor/digital -> better access & resilience, higher cost.
    - Higher shock_intensity -> worse access & resilience, slightly higher cost.
    """

    base_cost = 100.0

    cost_multiplier = (
        1.0
        + 0.8 * operating_model.staffing_level
        + 0.4 * operating_model.vendor_support
        + 0.2 * shock_intensity
    )

    total_cost = base_cost * cost_multiplier

    access_score = (
        60
        + 25 * operating_model.staffing_level
        + 10 * operating_model.digital_penetration
        - 30 * shock_intensity
    )

    resilience_margin = (
        50
        + 20 * operating_model.vendor_support
        + 10 * operating_model.staffing_level
        - 35 * shock_intensity
    )

    roi_score = (
        70
        + 10 * operating_model.digital_penetration
        - 15 * operating_model.risk_tolerance
        - 10 * shock_intensity
    )

    # clamp 0–100
    def clamp(x): return max(0, min(100, x))

    return KPIResult(
        total_cost=round(total_cost, 2),
        access_score=round(clamp(access_score), 1),
        resilience_margin=round(clamp(resilience_margin), 1),
        roi_score=round(clamp(roi_score), 1),
    )

def run_all_operating_models(shock_intensity: float) -> Dict[OperatingModelType, KPIResult]:
    models = get_default_operating_models()
    return {
        om_type: run_single_scenario(cfg, shock_intensity)
        for om_type, cfg in models.items()
    }