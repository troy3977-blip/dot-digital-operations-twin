import streamlit as st
import pandas as pd

from core.simulation import run_all_operating_models
from core.operating_models import OperatingModelType


def render() -> None:
    st.subheader("Scenario Matrix")

    shock_levels = {
        "Mild": 0.2,
        "Expected": 0.4,
        "Severe": 0.7,
        "Extreme": 0.9,
    }

    records = []

    for scenario_name, shock in shock_levels.items():
        results = run_all_operating_models(shock)
        for om_type, kpis in results.items():
            records.append(
                {
                    "Scenario": scenario_name,
                    "Operating Model": om_type.value,
                    "Total Cost": kpis.total_cost,
                    "Access Score": kpis.access_score,
                    "Resilience Margin": kpis.resilience_margin,
                    "ROI Score": kpis.roi_score,
                }
            )

    df = pd.DataFrame(records)
    st.markdown("### Scenario outcomes")
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        pivot = df.pivot_table(
            index="Scenario",
            columns="Operating Model",
            values="Resilience Margin",
        )
        st.markdown("### Resilience Margin by Scenario / Operating Model")
        st.dataframe(pivot, use_container_width=True)