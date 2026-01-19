import streamlit as st

from ui import policy_explorer, scenario_matrix, frontier_view


st.set_page_config(
    page_title="DOT – Digital Operations Twin",
    layout="wide",
)

st.title("DOT – Digital Operations Twin")
st.caption("A digital operations twin for strategic decision-making.")

view = st.sidebar.radio(
    "View",
    options=["Policy Explorer", "Scenario Matrix", "Trade-off Frontier"],
)

if view == "Policy Explorer":
    policy_explorer.render()
elif view == "Scenario Matrix":
    scenario_matrix.render()
else:
    frontier_view.render()
