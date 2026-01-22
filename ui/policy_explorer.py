import streamlit as st

from core.workforce_model import (
    WorkforceInputs,
    run_workforce_scenario,
)


def render() -> None:
    st.subheader("Digital Workforce Twin – Policy Explorer")

    st.markdown(
        "Adjust workforce levers to see how service level, backlog, cost, and resilience respond "
        "under different demand shocks."
    )

    col_input_levers, col_output_metrics = st.columns(2)

    with col_input_levers:
        fte = st.slider(
            "Total FTE",
            min_value=50,
            max_value=200,
            value=100,
            step=5,
            help="Total FTE across internal and vendor.",
        )
        automation_penetration = st.slider(
            "Automation penetration",
            min_value=0.0,
            max_value=0.8,
            value=0.4,
            step=0.05,
            help="Share of contacts deflected or handled by digital/self-service.",
        )
        vendor_fraction = st.slider(
            "Vendor fraction",
            min_value=0.0,
            max_value=0.8,
            value=0.3,
            step=0.05,
            help="Fraction of FTE delivered by vendor/outsourcing partners.",
        )

    with col_output_metrics:
        shrinkage = st.slider(
            "Shrinkage",
            min_value=0.20,
            max_value=0.40,
            value=0.30,
            step=0.01,
            help="Absence, training, meetings, etc. Higher shrinkage reduces effective capacity.",
        )
        demand_shock = st.slider(
            "Demand shock",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.05,
            help="0 = no shock; 1 = 100% increase in demand.",
        )

    inputs = WorkforceInputs(
        fte=fte,
        automation_penetration=automation_penetration,
        vendor_fraction=vendor_fraction,
        shrinkage=shrinkage,
        demand_shock=demand_shock,
    )

    kpis = run_workforce_scenario(inputs)

    st.markdown("### Workforce KPIs")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Service Level (80/60)", f"{kpis.service_level:.1f} %")
        st.metric("Average Wait", f"{kpis.avg_wait_seconds:.1f} s")
    with m2:
        st.metric("Backlog (queue size)", f"{kpis.backlog:.1f}")
        st.metric("Occupancy", f"{kpis.occupancy:.1f} %")
    with m3:
        st.metric("Cost per Hour", f"${kpis.cost_per_hour:,.2f}")
        st.metric("Resilience Margin", f"{kpis.resilience_margin:.1f} %")

    st.caption(
        "Service level is modeled as Erlang-C 80/60. Resilience margin reflects the capacity "
        "headroom after accounting for shrinkage, automation, and shock."
    )