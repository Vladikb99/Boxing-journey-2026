import streamlit as st


def metric_card(
    title: str,
    value: str,
    delta: str,
    page_url: str | None = None,
    animation_class: str = "",
) -> None:
    card_html = f"""
<div class="custom-metric-card {animation_class}">
<div class="metric-card-title">{title}</div>
<div class="metric-card-value">
    <span class="count-up-number" data-final="{value}">{value}</span>
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