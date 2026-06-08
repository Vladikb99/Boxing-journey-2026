import streamlit as st

from components.home_button import home_button
from components.page_header import page_header
from utils.settings_loader import load_settings, save_settings
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Settings", eyebrow="APP SETTINGS")
home_button()

st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)

settings = load_settings()

st.markdown(
    """
<div class="settings-card">
<div class="settings-eyebrow">USER PARAMETERS</div>
<div class="settings-title">Personal setup</div>
<div class="settings-subtitle">
Change the values used across the dashboard.
</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.form("settings_form"):
    user_name = st.text_input(
        "User name",
        value=settings["user_name"],
    )

    height_m = st.number_input(
        "Height (m)",
        min_value=1.20,
        max_value=2.30,
        value=float(settings["height_m"]),
        step=0.01,
    )

    start_weight = st.number_input(
        "Start weight (kg)",
        min_value=30.0,
        max_value=200.0,
        value=float(settings["start_weight"]),
        step=0.1,
    )

    goal_weight = st.number_input(
        "Goal weight (kg)",
        min_value=30.0,
        max_value=200.0,
        value=float(settings["goal_weight"]),
        step=0.1,
    )

    submitted = st.form_submit_button(
        "Save settings",
        use_container_width=True,
    )

    if submitted:
        new_settings = {
            "user_name": user_name.strip() or "User",
            "height_m": height_m,
            "start_weight": start_weight,
            "goal_weight": goal_weight,
        }

        save_settings(new_settings)

        st.success("Settings saved.")
        st.rerun()


st.markdown("</div>", unsafe_allow_html=True)