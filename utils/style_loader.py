from pathlib import Path

import streamlit as st


def load_css(file_path: str) -> None:
    css_path = Path(file_path)

    if not css_path.exists():
        st.warning(f"CSS file not found: {file_path}")
        return

    with open(css_path, "r", encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True
        )