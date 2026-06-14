from html import escape


def achievement_badges_html(
    eyebrow: str,
    title: str,
    detail: str,
    achievements: list[dict],
) -> str:
    badge_html = ""

    for achievement in achievements:
        name = escape(str(achievement["name"]))
        unlocked = bool(achievement["unlocked"])

        locked_class = "" if unlocked else " locked"
        badge_html += f'<span class="achievement-badge{locked_class}">{name}</span>'

    return f"""
<div class="polish-card soft-appear">
<div class="polish-eyebrow">{escape(eyebrow)}</div>
<div class="polish-title">{escape(title)}</div>
<div class="polish-subtitle">{escape(detail)}</div>

<div class="badge-row">
{badge_html}
</div>
</div>
"""


def achievement_popup_html(name: str, detail: str = "") -> str:
    detail_html = ""

    if detail:
        detail_html = f'<div class="achievement-popup-detail">{escape(detail)}</div>'

    return f"""
<div class="achievement-popup">
<div class="achievement-popup-top">Achievement unlocked</div>
<div class="achievement-popup-title">{escape(name)}</div>
{detail_html}
</div>
"""