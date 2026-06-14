from html import escape


def streak_card_html(
    eyebrow: str,
    title: str,
    current_streak: int,
    best_streak: int,
    detail: str,
) -> str:
    return f"""
<div class="polish-card soft-appear">
<div class="polish-eyebrow">{escape(eyebrow)}</div>
<div class="polish-title">{escape(title)}</div>
<div class="polish-subtitle">{escape(detail)}</div>

<div class="polish-grid">
<div class="streak-card">
<div class="streak-label">Current streak</div>
<div class="streak-number">{current_streak}</div>
<div class="streak-detail">weeks</div>
</div>

<div class="streak-card">
<div class="streak-label">Best streak</div>
<div class="streak-number">{best_streak}</div>
<div class="streak-detail">weeks</div>
</div>
</div>
</div>
"""