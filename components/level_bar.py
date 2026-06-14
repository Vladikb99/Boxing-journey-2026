from html import escape


def level_bar_html(
    eyebrow: str,
    title: str,
    percentage: float,
    label: str,
    detail: str,
) -> str:
    percentage = max(0, min(float(percentage), 100))

    return f"""
<div class="polish-card soft-appear">
<div class="polish-eyebrow">{escape(eyebrow)}</div>
<div class="polish-title">{escape(title)}</div>
<div class="polish-subtitle">{escape(detail)}</div>

<div class="level-bar-shell">
<div class="level-bar-fill" style="--level-width: {percentage:.1f}%;"></div>
</div>

<div class="level-row">
<div class="level-label">{escape(label)}</div>
<div class="level-value">{percentage:.0f}%</div>
</div>
</div>
"""