import streamlit as st
import plotly.express as px
import pandas as pd

from typing import Any

from core.simulation import run_all_operating_models


# Constants for slider configuration
SLIDER_MIN = 0.0
SLIDER_MAX = 1.0
SLIDER_DEFAULT = 0.5
SLIDER_STEP = 0.05


def render() -> None:
    """
    Renders the Trade-off Frontier (Cost vs Resilience) visualization in Streamlit.
    """
    st.subheader("Trade-off Frontier")

    shock_intensity = st.slider(
        "Shock intensity",
        min_value=SLIDER_MIN,
        max_value=SLIDER_MAX,
        value=SLIDER_DEFAULT,
        step=SLIDER_STEP,
        help="0 = no disruption, 1 = extreme disruption",
    )

    st.caption(
        "Each point represents an operating model. "
        "Move the slider to see how a larger shock shifts the cost vs resilience frontier."
    )

    results = run_all_operating_models(shock_intensity)

    data = [
        {
            "Operating Model": om_type.value,
            "Total Cost": kpis.total_cost,
            "Access Score": kpis.access_score,
            "Resilience Margin": kpis.resilience_margin,
            "ROI Score": kpis.roi_score,
        }
        for om_type, kpis in results.items()
    ]
    df = pd.DataFrame(data)

    if df.empty:
        st.info("No results to display.")
        return

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