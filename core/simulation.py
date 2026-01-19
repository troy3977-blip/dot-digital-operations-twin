from typing import Dict

from .kpis import KPIResult
from .operating_models import (
    OperatingModelConfig,
    OperatingModelType,
    get_default_operating_models,
)


def run_single_scenario(
    operating_model: OperatingModelConfig,
    shock_intensity: float,  # 0–1
) -> KPIResult:
    """
    Very simple, transparent mapping from operating-model levers and a shock
    intensity into four KPIs.

    Intent:
    - Higher staffing / vendor / digital -> better access & resilience, higher cost.
    - Higher shock_intensity -> worse access & resilience, slightly higher cost.
    - risk_tolerance shifts how hard the shock hits service / resilience.

    This is deliberately simplistic; the point is to support interactive exploration,
    not to be a production-grade forecasting engine.
    """
    shock = max(0.0, min(1.0, shock_intensity))

    # Cost: indexed around 100. Higher staffing/vendor/digital increases cost.
    base_cost_index = 100.0
    cost_uplift = (
        0.5 * operating_model.staffing_level
        + 0.3 * operating_model.vendor_support
        + 0.2 * operating_model.digital_penetration
        + 0.2 * shock
    )
    total_cost = base_cost_index * (1.0 + cost_uplift)

    # Access: starts from 70 and is helped by digital + staffing, hurt by shock.
    access_score = (
        70.0
        + 20.0 * operating_model.digital_penetration
        + 10.0 * operating_model.staffing_level
        - 35.0 * shock * (0.7 + 0.3 * operating_model.risk_tolerance)
    )

    # Resilience: driven by staffing, vendor support, and lower risk tolerance.
    resilience_margin = (
        50.0
        + 20.0 * operating_model.staffing_level
        + 15.0 * operating_model.vendor_support
        + 10.0 * (1.0 - operating_model.risk_tolerance)
        - 40.0 * shock
    )

    # ROI: reward digital + vendor, penalise very high cost.
    roi_score = (
        60.0
        + 20.0 * operating_model.digital_penetration
        + 10.0 * operating_model.vendor_support
        - 0.25 * max(0.0, total_cost - 100.0)
    )

    def clamp_0_100(x: float) -> float:
        return max(0.0, min(100.0, x))

    return KPIResult(
        total_cost=round(total_cost, 2),
        access_score=round(clamp_0_100(access_score), 1),
        resilience_margin=round(clamp_0_100(resilience_margin), 1),
        roi_score=round(clamp_0_100(roi_score), 1),
    )


def run_all_operating_models(shock_intensity: float) -> Dict[OperatingModelType, KPIResult]:
    """
    Convenience helper for multi-model comparisons.
    """
    models = get_default_operating_models()
    return {
        om_type: run_single_scenario(cfg, shock_intensity)
        for om_type, cfg in models.items()
    }