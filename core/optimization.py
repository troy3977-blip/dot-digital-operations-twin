from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

from .workforce_model import (
    WorkforceInputs,
    WorkforceKPIResult,
    run_workforce_scenario,
)


@dataclass
class OptimizationCandidate:
    inputs: WorkforceInputs
    kpis: WorkforceKPIResult


@dataclass
class OptimizationResult:
    objective_value: float
    candidate: OptimizationCandidate
    explored_count: int


# --- Search space helpers ---


def _default_search_grid() -> Dict[str, List]:
    """
    Defines a coarse search grid over workforce levers.
    Tune these ranges/steps based on your sense of what's realistic.
    """
    fte_values = list(range(70, 151, 5))  # 70, 75, ... 150
    automation_values = [round(x, 2) for x in [i * 0.05 for i in range(0, 13)]]  # 0.0 .. 0.6
    vendor_values = [0.2, 0.3, 0.4]  # simple mix options
    shrinkage_values = [0.26, 0.30, 0.34]  # reasonable band

    return {
        "fte": fte_values,
        "automation": automation_values,
        "vendor_fraction": vendor_values,
        "shrinkage": shrinkage_values,
    }


# --- Mode A: minimize cost subject to service-level constraint ---


def optimize_min_cost_for_service(
    target_service_level: float,
    demand_shock: float,
    search_grid: Optional[Dict[str, List]] = None,
) -> Optional[OptimizationResult]:
    """
    Find the lowest-cost configuration that achieves at least target_service_level (%)
    at a given demand_shock.

    Returns None if nothing in the grid meets the constraint.
    """
    if search_grid is None:
        search_grid = _default_search_grid()

    best: Optional[OptimizationResult] = None
    explored = 0

    for fte in search_grid["fte"]:
        for automation in search_grid["automation"]:
            for vendor_fraction in search_grid["vendor_fraction"]:
                for shrinkage in search_grid["shrinkage"]:
                    inputs = WorkforceInputs(
                        fte=fte,
                        automation_penetration=automation,
                        vendor_fraction=vendor_fraction,
                        shrinkage=shrinkage,
                        demand_shock=demand_shock,
                    )
                    kpis = run_workforce_scenario(inputs)
                    explored += 1

                    if kpis.service_level < target_service_level:
                        continue

                    obj = kpis.cost_per_hour  # minimize cost
                    if best is None or obj < best.objective_value:
                        best = OptimizationResult(
                            objective_value=obj,
                            candidate=OptimizationCandidate(inputs=inputs, kpis=kpis),
                            explored_count=explored,
                        )

    return best


# --- Mode B: maximize service (and resilience) subject to cost cap ---


def optimize_max_service_under_cost(
    max_cost_per_hour: float,
    demand_shock: float,
    search_grid: Optional[Dict[str, List]] = None,
) -> Optional[OptimizationResult]:
    """
    Among configurations under a cost cap, pick the one with highest service level.
    If service is tied, prefer higher resilience.
    """
    if search_grid is None:
        search_grid = _default_search_grid()

    best: Optional[OptimizationResult] = None
    explored = 0

    for fte in search_grid["fte"]:
        for automation in search_grid["automation"]:
            for vendor_fraction in search_grid["vendor_fraction"]:
                for shrinkage in search_grid["shrinkage"]:
                    inputs = WorkforceInputs(
                        fte=fte,
                        automation_penetration=automation,
                        vendor_fraction=vendor_fraction,
                        shrinkage=shrinkage,
                        demand_shock=demand_shock,
                    )
                    kpis = run_workforce_scenario(inputs)
                    explored += 1

                    if kpis.cost_per_hour > max_cost_per_hour:
                        continue

                    score = (kpis.service_level, kpis.resilience_margin)

                    if best is None:
                        best = OptimizationResult(
                            objective_value=kpis.service_level,
                            candidate=OptimizationCandidate(inputs=inputs, kpis=kpis),
                            explored_count=explored,
                        )
                    else:
                        best_sl = best.candidate.kpis.service_level
                        best_res = best.candidate.kpis.resilience_margin
                        if (kpis.service_level > best_sl) or (
                            kpis.service_level == best_sl
                            and kpis.resilience_margin > best_res
                        ):
                            best = OptimizationResult(
                                objective_value=kpis.service_level,
                                candidate=OptimizationCandidate(inputs=inputs, kpis=kpis),
                                explored_count=explored,
                            )

    return best


# --- Mode C: Pareto frontier for Cost vs Service ---


def compute_pareto_frontier(
    demand_shock: float,
    search_grid: Optional[Dict[str, List]] = None,
) -> List[OptimizationCandidate]:
    """
    Compute a Pareto frontier in (cost, service_level) space.
    A point A dominates B if:
        cost_A <= cost_B and service_A >= service_B
        and at least one inequality is strict.
    Returns a list of non-dominated candidates.
    """
    if search_grid is None:
        search_grid = _default_search_grid()

    candidates: List[OptimizationCandidate] = []

    for fte in search_grid["fte"]:
        for automation in search_grid["automation"]:
            for vendor_fraction in search_grid["vendor_fraction"]:
                for shrinkage in search_grid["shrinkage"]:
                    inputs = WorkforceInputs(
                        fte=fte,
                        automation_penetration=automation,
                        vendor_fraction=vendor_fraction,
                        shrinkage=shrinkage,
                        demand_shock=demand_shock,
                    )
                    kpis = run_workforce_scenario(inputs)
                    candidates.append(OptimizationCandidate(inputs=inputs, kpis=kpis))

    # Filter non-dominated set
    pareto: List[OptimizationCandidate] = []
    for c in candidates:
        dominated = False
        for other in candidates:
            if other is c:
                continue
            if (
                other.kpis.cost_per_hour <= c.kpis.cost_per_hour
                and other.kpis.service_level >= c.kpis.service_level
                and (
                    other.kpis.cost_per_hour < c.kpis.cost_per_hour
                    or other.kpis.service_level > c.kpis.service_level
                )
            ):
                dominated = True
                break
        if not dominated:
            pareto.append(c)

    # Optional: sort frontier by cost ascending
    pareto.sort(key=lambda cand: cand.kpis.cost_per_hour)
    return pareto