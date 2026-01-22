from core.optimization import optimize_min_cost_for_service
from core.workforce_model import WorkforceInputs, WorkforceKPIResult
from core.optimization import optimize_max_service_under_cost

import streamlit as st
import pandas as pd
import plotly.express as px

from core.workforce_model import (
    get_default_policies,
    run_policies_for_shock,
)


def render() -> None:
    st.subheader("Trade-off Frontier – Cost vs Service vs Resilience")

    st.markdown(
        "Visualize the cost–service–resilience frontier for different workforce policies under a "
        "single demand shock. Each point is a policy; bubble size represents resilience."
    )

    demand_shock = st.slider(
        "Demand shock",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.05,
        help="0 = no shock; 1 = 100% increase in demand.",
    )

    policies = get_default_policies()
    results = run_policies_for_shock(demand_shock, policies)

    data = [
        {
            "Policy": policy_name,
            "Service Level (80/60)": kpis.service_level,
            "Cost per Hour": kpis.cost_per_hour,
            "Resilience Margin": kpis.resilience_margin,
            "Backlog": kpis.backlog,
            "Occupancy": kpis.occupancy,
        }
        for policy_name, kpis in results.items()
    ]
    df = pd.DataFrame(data)

    if df.empty:
        st.info("No results to display.")
        return

    fig = px.scatter(
        df,
        x="Cost per Hour",
        y="Service Level (80/60)",
        color="Policy",
        size="Resilience Margin",
        hover_data=["Backlog", "Occupancy"],
        labels={
            "Cost per Hour": "Cost per Hour ($)",
            "Service Level (80/60)": "Service Level 80/60 (%)",
        },
        title="Cost vs Service Level (bubble size = Resilience Margin)",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Higher bubbles indicate more resilience (capacity headroom). The goal is to move "
        "toward the upper-left region: high service level at lower cost with sufficient resilience."
    )

    st.markdown("### Recommendation – Cheapest way to hit a service target")

    target_sl = st.slider(
        "Target service level (80/60)",
        min_value=60.0,
        max_value=95.0,
        value=80.0,
        step=1.0,
    )

    if st.button("Find recommended configuration"):
        with st.spinner("Searching configuration space..."):
            opt = optimize_min_cost_for_service(
                target_service_level=target_sl,
                demand_shock=demand_shock,
            )

        if opt is None:
            st.warning(
                "No configuration in the current search grid can hit "
                f"{target_sl:.1f}% service at this shock level."
            )
        else:
            cand = opt.candidate
            inp: WorkforceInputs = cand.inputs
            kpis: WorkforceKPIResult = cand.kpis

            st.success(
                f"Found configuration after exploring {opt.explored_count} candidates."
            )

            col_inputs, col_kpis = st.columns(2)
            with col_inputs:
                st.markdown("**Recommended levers**")
                st.markdown(f"- FTE: **{inp.fte:.1f}**")
                st.markdown(f"- Automation penetration: **{inp.automation_penetration:.2f}**")
                st.markdown(f"- Vendor fraction: **{inp.vendor_fraction:.2f}**")
                st.markdown(f"- Shrinkage: **{inp.shrinkage:.2f}**")
                st.markdown(f"- Demand shock: **{inp.demand_shock:.2f}**")

            with col_kpis:
                st.markdown("**Expected outcomes**")
                st.markdown(f"- Service level (80/60): **{kpis.service_level:.1f}%**")
                st.markdown(f"- Avg wait: **{kpis.avg_wait_seconds:.1f} s**")
                st.markdown(f"- Backlog: **{kpis.backlog:.1f}**")
                st.markdown(f"- Occupancy: **{kpis.occupancy:.1f}%**")
                st.markdown(f"- Cost per hour: **${kpis.cost_per_hour:,.2f}**")
                st.markdown(f"- Resilience margin: **{kpis.resilience_margin:.1f}%**")

    st.markdown("### Recommendation – Max service under a cost cap")

    max_cost = st.number_input(
        "Max labor + digital cost per hour ($)",
        min_value=2000.0,
        max_value=10000.0,
        value=5000.0,
        step=250.0,
    )

    if st.button("Find best configuration under cost cap"):
        with st.spinner("Searching configuration space..."):
            opt2 = optimize_max_service_under_cost(
                max_cost_per_hour=max_cost,
                demand_shock=demand_shock,
            )

        if opt2 is None:
            st.warning(
                "No configuration in the current search grid stays under that cost cap."
            )
        else:
            cand2 = opt2.candidate
            inp2 = cand2.inputs
            kpis2 = cand2.kpis

            st.success(
                f"Best configuration under ${max_cost:,.0f}/hr cost cap "
                f"delivers {kpis2.service_level:.1f}% service level."
            )

            # display inp2 / kpis2 similar to above
