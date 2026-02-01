import streamlit as st

from ui import policy_explorer, scenario_matrix, frontier_view
import os
from kv import load_settings_from_key_vault, Settings

st.set_page_config(page_title="Digital Operating Twin", layout="wide")

@st.cache_resource(show_spinner=False)
def get_settings() -> Settings:
    """
    Cache secrets client-side per Streamlit session process.
    Avoid fetching from Key Vault on every rerun.
    """
    # Optional: allow bypass for quick local dev
    if os.getenv("SKIP_KEY_VAULT", "").lower() in ("1", "true", "yes"):
        return Settings(
            sql_conn_str=os.getenv("SQL_CONN_STR"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            some_third_party_key=os.getenv("THIRD_PARTY_API_KEY"),
        )

    return load_settings_from_key_vault()

settings = get_settings()

# Example: assert required secrets (or just warn)
if not settings.sql_conn_str:
    st.warning("SQL connection string not found (Key Vault secret: sql-conn-str). Running in degraded mode.")

# Use settings in your app
st.title("DOT – Digital Operations Twin")
st.caption("A digital operations twin for strategic decision-making.")

with st.expander("Debug: config status", expanded=False):
    st.write(
        {
            "key_vault_name": os.getenv("KEYVAULT_NAME"),
            "has_sql_conn_str": bool(settings.sql_conn_str),
            "has_openai_api_key": bool(settings.openai_api_key),
        }
    )

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
