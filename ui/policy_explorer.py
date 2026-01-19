import streamlit as st
import plotly.graph_objects as go

from core.simulation import run_single_scenario
from core.operating_models import get_default_operating_models, OperatingModelType


def render() -> None:
    st.subheader("Policy Explorer")

    models = get_default_operating_models()

    model_choice: OperatingModelType = st.selectbox(
        "Operating model",
        options=list(models.keys()),
        format_func=lambda x: models[x].name,
    )

    shock_intensity = st.slider(
        "Shock intensity",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.05,
        help="0 = no disruption, 1 = extreme disruption",
    )

    cfg = models[model_choice]
    kpis = run_single_scenario(cfg, shock_intensity)

    st.markdown("### KPIs")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Cost (index)", f"{kpis.total_cost:.1f}")
        st.metric("Access Score", f"{kpis.access_score:.1f}")
    with col2:
        st.metric("Resilience Margin", f"{kpis.resilience_margin:.1f}")
        st.metric("ROI Score", f"{kpis.roi_score:.1f}")

    st.markdown("### Resilience Gauge")
    fig = go.Figure()
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis.resilience_margin,
            title={"text": "Resilience Margin"},
            gauge={"axis": {"range": [0, 100]}},
        )
    )
    st.plotly_chart(fig, use_container_width=True)
