import streamlit as st
from utils.data_loader import load_weight_data, get_latest_weight
from utils.calculations import calculate_weight_change

# Page configuration

st.set_page_config(
    page_title="Boxing Journey 2026",
    layout="wide"
)

# Sample data

# Load weight data
weight_df = load_weight_data()
weight = f"{get_latest_weight()} kg"
weight_change = calculate_weight_change(weight_df)

last_run = "4 km"
last_pace = "5:27/km"

boxing_sessions = "0 this week"
boxing_note = "No session logged"

gym_sessions = "0 this week"
gym_note = "No session logged"


def metric_card(label, value, delta):
    st.metric(
        label=label,
        value=value,
        delta=delta
    )

# Title

st.title("BOXING JOURNEY 2026")

st.subheader("Welcome back")
st.divider()

col1, col2 = st.columns(2)

with col1:
    metric_card(
        label="Weight",
        value=weight,
        delta=weight_change
    )

with col2:
    metric_card(
        label="Last Run",
        value=last_run,
        delta=last_pace
    )

col3, col4 = st.columns(2)

with col3:
    metric_card("Boxing", boxing_sessions, boxing_note)

with col4:
    metric_card("Gym", gym_sessions, gym_note)