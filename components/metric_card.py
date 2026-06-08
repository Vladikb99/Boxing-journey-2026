import base64
from pathlib import Path

import streamlit as st


def _image_to_base64(image_path: str) -> str:
    path = Path(image_path)

    if not path.exists():
        return ""

    return base64.b64encode(path.read_bytes()).decode()


def metric_card(
    title: str,
    value: str,
    delta: str,
    icon_path: str,
    page_url: str | None = None,
) -> None:
    icon_base64 = _image_to_base64(icon_path)

    card_html = f"""
<div class="custom-metric-card">
<img class="metric-card-icon" src="data:image/png;base64,{icon_base64}" alt="{title} icon">
<div class="metric-card-title">{title}</div>
<div class="metric-card-value">{value}</div>
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