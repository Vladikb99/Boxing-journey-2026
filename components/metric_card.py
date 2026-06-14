import re

import streamlit as st


def _initial_zero_value(value: str) -> str:
    text = str(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", text)

    if not match:
        return text

    number_text = match.group(0)
    decimals = 0

    if "." in number_text:
        decimals = len(number_text.split(".")[1])
    elif "," in number_text:
        decimals = len(number_text.split(",")[1])

    zero_value = f"{0:.{decimals}f}"

    if "," in number_text:
        zero_value = zero_value.replace(".", ",")

    return text[:match.start()] + zero_value + text[match.end():]


def metric_card(
    title: str,
    value: str,
    delta: str,
    page_url: str | None = None,
    animation_class: str = "",
) -> None:
    initial_value = _initial_zero_value(value)

    card_html = f"""
<div class="custom-metric-card {animation_class}">
<div class="metric-card-title">{title}</div>
<div class="metric-card-value">
    <span class="count-up-number" data-final="{value}">{initial_value}</span>
</div>
<div class="metric-card-delta">{delta}</div>
</div>
"""

    if page_url:
        card_html = f"""
<a class="metric-card-link" href="{page_url}" target="_self">
{card_html}
</a>
"""

    st.markdown(card_html, unsafe_allow_html=True)