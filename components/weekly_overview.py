import html
import re

import streamlit as st


def _zero_display(value: str) -> str:
    value = str(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", value)

    if not match:
        return value

    number_text = match.group(0).replace(",", ".")

    decimals = 0
    if "." in number_text:
        decimals = len(number_text.split(".")[1])

    zero_text = f"{0:.{decimals}f}"

    return value[: match.start()] + zero_text + value[match.end() :]


def _countup_span(value: str) -> str:
    safe_value = html.escape(str(value))
    safe_zero_value = html.escape(_zero_display(str(value)))

    return f'<span class="count-up-number" data-final="{safe_value}">{safe_zero_value}</span>'


def weekly_overview(
    weight_change: str,
    run_distance: str,
    boxing_sessions: str,
    gym_sessions: str,
    animation_class: str = "",
) -> None:
    html_output = f"""
<div class="weekly-strip {animation_class}">
<div class="weekly-label">LAST 7 DAYS</div>
<div class="weekly-grid">

<div>
    <div class="weekly-title">Weight</div>
    <div class="weekly-value">{_countup_span(weight_change)}</div>
</div>

<div>
    <div class="weekly-title">Runs</div>
    <div class="weekly-value">{_countup_span(run_distance)}</div>
</div>

<div>
    <div class="weekly-title">Boxing</div>
    <div class="weekly-value">{_countup_span(boxing_sessions)}</div>
</div>

<div>
    <div class="weekly-title">Gym</div>
    <div class="weekly-value">{_countup_span(gym_sessions)}</div>
</div>

</div>
</div>
"""
    st.markdown(html_output, unsafe_allow_html=True)