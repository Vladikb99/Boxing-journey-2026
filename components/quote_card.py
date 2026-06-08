import streamlit as st


def quote_card(quote: str, author: str) -> None:
    html = f"""
<div class="premium-quote-card">
<div class="quote-mark-open">❝</div>
<div class="premium-quote-body">
<div class="premium-quote-text">{quote}</div>
<div class="premium-quote-bottom">
<div class="quote-mark-close">❞</div>
<div class="premium-quote-author">— {author}</div>
</div>
</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)