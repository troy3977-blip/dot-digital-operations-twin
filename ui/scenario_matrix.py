import streamlit as st
import pandas as pd

from core.workforce_model import (
    get_default_policies,
    run_policies_for_shock,
)


def render() -> None:
    st.subheader("Scenario Matrix – Workforce Policies vs Demand Shocks")

    st.markdown(
        "Compare Lean, Balanced, and Resilient workforce policies across different demand shocks. "
        "This view highlights how service level, backlog, and cost change under stress."
    )

    policies = get_default_policies()
    shocks = {
        "Mild (+10%)": 0.10,
        "Expected (+30%)": 0.30,
        "Severe (+60%)": 0.60,
        "Extreme (+100%)": 1.00,
    }

    records = []
    for scenario_name, shock in shocks.items():
        results = run_policies_for_shock(shock, policies)
        for policy_name, kpis in results.items():
            records.append(
                {
                    "Scenario": scenario_name,
                    "Policy": policy_name,
                    "Service Level (80/60)": kpis.service_level,
                    "Avg Wait (s)": kpis.avg_wait_seconds,
                    "Backlog": kpis.backlog,
                    "Occupancy (%)": kpis.occupancy,
                    "Cost per Hour ($)": kpis.cost_per_hour,
                    "Resilience Margin (%)": kpis.resilience_margin,
                }
            )

    df = pd.DataFrame(records)

    st.markdown("### Scenario Outcomes")
    st.dataframe(df, use_container_width=True)

    st.markdown("### Service Level by Scenario and Policy")
    pivot_sl = df.pivot_table(
        index="Scenario",
        columns="Policy",
        values="Service Level (80/60)",
    )
    st.dataframe(pivot_sl.style.format("{:.1f}"), use_container_width=True)

    st.markdown("### Cost per Hour by Scenario and Policy")
    pivot_cost = df.pivot_table(
        index="Scenario",
        columns="Policy",
        values="Cost per Hour ($)",
    )
    st.dataframe(pivot_cost.style.format("${:,.0f}"), use_container_width=True)