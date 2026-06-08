import streamlit as st


def home_button() -> None:
    st.markdown(
        """
<a class="home-button" href="/?skip_splash=true" target="_self">
← Home
</a>
""",
        unsafe_allow_html=True,
    )