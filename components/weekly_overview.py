import streamlit as st


def weekly_overview(
    weight_change: str,
    run_distance: str,
    boxing_sessions: str,
    gym_sessions: str,
    animation_class: str = "",
) -> None:
    html = f"""
<div class="weekly-strip {animation_class}">
<div class="weekly-label">LAST 7 DAYS</div>
<div class="weekly-grid">

<div>
    <div class="weekly-title">Weight</div>
    <div class="weekly-value">
        <span class="count-up-number" data-final="{weight_change}">{weight_change}</span>
    </div>
</div>

<div>
    <div class="weekly-title">Runs</div>
    <div class="weekly-value">
        <span class="count-up-number" data-final="{run_distance}">{run_distance}</span>
    </div>
</div>

<div>
    <div class="weekly-title">Boxing</div>
    <div class="weekly-value">
        <span class="count-up-number" data-final="{boxing_sessions}">{boxing_sessions}</span>
    </div>
</div>

<div>
    <div class="weekly-title">Gym</div>
    <div class="weekly-value">
        <span class="count-up-number" data-final="{gym_sessions}">{gym_sessions}</span>
    </div>
</div>

</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)