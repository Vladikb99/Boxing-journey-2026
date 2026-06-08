import streamlit as st


def quote_card(quote: str, author: str) -> None:
    html = f"""
<div class="premium-quote-card">
<div class="quote-mark">❝</div>
<div class="premium-quote-text">{quote}</div>
<div class="quote-mark">❝</div>
<div class="premium-quote-author">— {author}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)