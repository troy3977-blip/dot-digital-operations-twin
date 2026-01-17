import streamlit as st
import plotly.express as px
import pandas as pd
from core.simulation import run_all_operating_models

def render():
    st.subheader("Trade-off Frontier (Cost vs Resilience)")

    shock_intensity = st.slider(
        "Shock intensity for frontier view",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
    )

    results = run_all_operating_models(shock_intensity)
    data = []
    for om_type, kpis in results.items():
        data.append({
            "Operating Model": om_type.value,
            "Total Cost": kpis.total_cost,
            "Resilience Margin": kpis.resilience_margin,
            "Access Score": kpis.access_score,
            "ROI Score": kpis.roi_score,
        })
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