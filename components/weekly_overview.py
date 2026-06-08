import streamlit as st


def weekly_overview(
    weight_change: str,
    run_distance: str,
    boxing_sessions: str,
    gym_sessions: str,
) -> None:
    html = f"""
<div class="weekly-strip">
<div class="weekly-label">LAST 7 DAYS</div>
<div class="weekly-grid">
<div><div class="weekly-title">Weight</div><div class="weekly-value">{weight_change}</div></div>
<div><div class="weekly-title">Runs</div><div class="weekly-value">{run_distance}</div></div>
<div><div class="weekly-title">Boxing</div><div class="weekly-value">{boxing_sessions}</div></div>
<div><div class="weekly-title">Gym</div><div class="weekly-value">{gym_sessions}</div></div>
</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)