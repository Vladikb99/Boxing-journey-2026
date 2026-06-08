import streamlit as st


def page_header(title: str, eyebrow: str | None = None) -> None:
    eyebrow_text = eyebrow or f"{title.upper()} TRACKING"

    st.markdown(
        f"""
<div class="page-header">
<div>
<div class="page-header-eyebrow">{eyebrow_text}</div>
<div class="page-header-title">{title}</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )