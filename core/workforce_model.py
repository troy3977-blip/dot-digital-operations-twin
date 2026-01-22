from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import math


# --- Domain constants (you can tweak these later) ---

AHT_SECONDS = 420.0                     # Given: 420s
SERVICE_LEVEL_THRESHOLD_SECONDS = 60.0  # Given: 80/60
BASE_VOLUME_PER_HOUR = 500.0            # Baseline demand
BASE_FTE = 100.0                        # Baseline staffing (FTE)

COST_PER_INTERNAL_FTE_HOUR = 35.0
COST_PER_VENDOR_FTE_HOUR = 30.0
DIGITAL_COST_PER_CONTACT = 0.20         # Approximate marginal cost
DIGITAL_DEFLECTION_EFFECTIVENESS = 0.7  # 70% of digital is effective deflection


# --- Data structures ---


@dataclass
class WorkforceInputs:
    """Inputs for a single workforce scenario."""
    fte: float                     # total FTE (internal + vendor)
    automation_penetration: float  # 0–1
    vendor_fraction: float         # 0–1 (fraction of FTE that is vendor)
    shrinkage: float               # 0–1
    demand_shock: float            # 0–1, where 0=no shock, 1=full shock


@dataclass
class WorkforceKPIResult:
    """Outputs/KPIs for a workforce scenario."""
    service_level: float           # 0–100 (%)
    avg_wait_seconds: float        # seconds
    backlog: float                 # expected queue length (contacts)
    occupancy: float               # 0–100 (%)
    cost_per_hour: float           # absolute $
    resilience_margin: float       # 0–100 (% capacity headroom)


@dataclass
class WorkforcePolicy:
    """A named configuration of levers."""
    name: str
    fte: float
    automation_penetration: float
    vendor_fraction: float
    shrinkage: float


# --- Erlang-C utilities ---


def _erlang_c(lambda_hr: float, mu_hr: float, n: float) -> float:
    """
    Compute Erlang-C waiting probability Pc for an M/M/n queue.

    lambda_hr: arrival rate per hour
    mu_hr: service rate per hour (1 / AHT_hours)
    n: number of agents (FTE effective)

    Returns:
        Pc (probability that an arrival has to wait)
    """
    if lambda_hr <= 0 or n <= 0:
        return 0.0

    # Use integer servers; if n<1, treat as 1.
    n_int = max(1, int(round(n)))
    a = lambda_hr / mu_hr  # offered load in erlangs

    # Unstable system: demand >= capacity
    if n_int <= a:
        return 1.0

    # Compute P0
    sum_terms = 0.0
    for k in range(n_int):
        sum_terms += (a ** k) / math.factorial(k)

    last_term = (a ** n_int) / (
        math.factorial(n_int) * (1.0 - (a / n_int))
    )
    p0 = 1.0 / (sum_terms + last_term)

    # Erlang C: Pc
    pc = last_term * p0
    return pc


def _service_level(
    lambda_hr: float,
    mu_hr: float,
    n: float,
    threshold_seconds: float,
) -> float:
    """Compute service level: P(wait <= threshold)."""
    if lambda_hr <= 0 or n <= 0:
        return 1.0

    n_int = max(1, int(round(n)))
    a = lambda_hr / mu_hr

    if n_int <= a:
        return 0.0

    pc = _erlang_c(lambda_hr, mu_hr, n_int)
    t_hr = threshold_seconds / 3600.0
    exponent = -(n_int * mu_hr - lambda_hr) * t_hr
    # Protect against under/overflow
    exponent = max(-700.0, min(700.0, exponent))
    sl = 1.0 - pc * math.exp(exponent)
    return max(0.0, min(1.0, sl))


def _queue_metrics(
    lambda_hr: float,
    mu_hr: float,
    n: float,
) -> tuple[float, float, float]:
    """
    Returns (avg_wait_seconds, backlog, occupancy%).

    avg_wait_seconds: expected queue waiting time
    backlog: expected queue length Lq
    occupancy: 0–1
    """
    if lambda_hr <= 0 or n <= 0:
        return 0.0, 0.0, 0.0

    n_int = max(1, int(round(n)))
    a = lambda_hr / mu_hr
    # True occupancy
    rho = a / n_int

    if n_int <= a:
        # Overloaded: very high waits & backlog, clamp occupancy > 100%
        return 3600.0, lambda_hr, 1.0

    pc = _erlang_c(lambda_hr, mu_hr, n_int)
    # Average wait in hours (Erlang-C formula)
    wq_hr = pc / (n_int * mu_hr - lambda_hr)
    avg_wait_seconds = max(0.0, wq_hr * 3600.0)
    backlog = max(0.0, lambda_hr * wq_hr)
    occupancy = max(0.0, min(1.0, rho))
    return avg_wait_seconds, backlog, occupancy


# --- Scenario computation ---


def run_workforce_scenario(inputs: WorkforceInputs) -> WorkforceKPIResult:
    """
    Compute KPIs for a single workforce scenario using Erlang-C and simple cost logic.
    """
    # Service parameters
    aht_hr = AHT_SECONDS / 3600.0
    mu_hr = 1.0 / aht_hr

    # Demand: baseline scaled by shock, then reduced by automation
    raw_lambda_hr = BASE_VOLUME_PER_HOUR * (1.0 + inputs.demand_shock)
    effective_deflection = inputs.automation_penetration * DIGITAL_DEFLECTION_EFFECTIVENESS
    effective_lambda_hr = raw_lambda_hr * (1.0 - effective_deflection)

    # Effective FTE after shrinkage
    effective_fte = max(1.0, inputs.fte * (1.0 - inputs.shrinkage))

    # Queue metrics
    sl = _service_level(effective_lambda_hr, mu_hr, effective_fte, SERVICE_LEVEL_THRESHOLD_SECONDS)
    avg_wait_seconds, backlog, occupancy = _queue_metrics(
        effective_lambda_hr, mu_hr, effective_fte
    )

    # Capacity and resilience
    capacity_hr = effective_fte * mu_hr
    if capacity_hr <= 0:
        resilience_margin = 0.0
    else:
        headroom = max(0.0, capacity_hr - effective_lambda_hr)
        resilience_margin = 100.0 * (headroom / capacity_hr)

    # Cost: FTE + vendor + digital
    internal_fte = inputs.fte * (1.0 - inputs.vendor_fraction)
    vendor_fte = inputs.fte * inputs.vendor_fraction

    cost_internal = internal_fte * COST_PER_INTERNAL_FTE_HOUR
    cost_vendor = vendor_fte * COST_PER_VENDOR_FTE_HOUR
    digital_contacts_per_hr = raw_lambda_hr * effective_deflection
    cost_digital = digital_contacts_per_hr * DIGITAL_COST_PER_CONTACT

    cost_per_hour = cost_internal + cost_vendor + cost_digital

    return WorkforceKPIResult(
        service_level=round(sl * 100.0, 1),
        avg_wait_seconds=round(avg_wait_seconds, 1),
        backlog=round(backlog, 1),
        occupancy=round(occupancy * 100.0, 1),
        cost_per_hour=round(cost_per_hour, 2),
        resilience_margin=round(resilience_margin, 1),
    )


# --- Default policies & helpers ---


def get_default_policies() -> Dict[str, WorkforcePolicy]:
    """
    Define three reference policies (Lean, Balanced, Resilient)
    over the same baseline environment.
    """
    return {
        "Lean": WorkforcePolicy(
            name="Lean",
            fte=BASE_FTE * 0.85,
            automation_penetration=0.30,
            vendor_fraction=0.25,
            shrinkage=0.32,
        ),
        "Balanced": WorkforcePolicy(
            name="Balanced",
            fte=BASE_FTE * 1.0,
            automation_penetration=0.40,
            vendor_fraction=0.30,
            shrinkage=0.30,
        ),
        "Resilient": WorkforcePolicy(
            name="Resilient",
            fte=BASE_FTE * 1.15,
            automation_penetration=0.50,
            vendor_fraction=0.35,
            shrinkage=0.28,
        ),
    }


def run_policies_for_shock(
    demand_shock: float,
    policies: Dict[str, WorkforcePolicy] | None = None,
) -> Dict[str, WorkforceKPIResult]:
    """
    Evaluate all policies under a given demand shock.
    """
    if policies is None:
        policies = get_default_policies()

    results: Dict[str, WorkforceKPIResult] = {}
    for policy_name, policy in policies.items():
        inputs = WorkforceInputs(
            fte=policy.fte,
            automation_penetration=policy.automation_penetration,
            vendor_fraction=policy.vendor_fraction,
            shrinkage=policy.shrinkage,
            demand_shock=demand_shock,
        )
        results[policy_name] = run_workforce_scenario(inputs)
    return results


def get_policy_names() -> List[str]:
    return list(get_default_policies().keys())