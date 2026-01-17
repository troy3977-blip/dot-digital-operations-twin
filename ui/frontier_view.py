import streamlit as st
import plotly.express as px
import pandas as pd
from core.simulation import run_all_operating_models
from typing import Any

# Constants for slider configuration
SLIDER_MIN = 0.0
SLIDER_MAX = 1.0
SLIDER_DEFAULT = 0.5
SLIDER_STEP = 0.05

def render() -> None:
    """
    Renders the Trade-off Frontier (Cost vs Resilience) visualization in Streamlit.
    """
    st.subheader("Trade-off Frontier (Cost vs Resilience)")

    shock_intensity: float = st.slider(
        "Shock intensity for frontier view",
        min_value=SLIDER_MIN,
        max_value=SLIDER_MAX,
        value=SLIDER_DEFAULT,
        step=SLIDER_STEP,
    )

    try:
        results: dict[str, Any] = run_all_operating_models(shock_intensity)
    except Exception as e:
        st.error(f"Error running simulation: {e}")
        return

    data = [
        {
            "Operating Model": om_type.value,
            "Total Cost": kpis.total_cost,
            "Resilience Margin": kpis.resilience_margin,
            "Access Score": kpis.access_score,
            "ROI Score": kpis.roi_score,
        }
        for om_type, kpis in results.items()
    ]
    df = pd.DataFrame(data)

    fig = px.scatter(
        df,
        x="Total Cost",
        y="Resilience Margin",
        text="Operating Model",
        size="ROI Score",
        hover_data=["Access Score"],
        title="Cost vs Resilience (bubble size = ROI)",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)
