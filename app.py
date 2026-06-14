import base64
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components.metric_card import metric_card
from components.quote_card import quote_card
from components.weekly_overview import weekly_overview
from config import APP_NAME, APP_YEAR
from utils.achievements import build_achievements as build_data_achievements
from utils.calculations import (
    calculate_last_7_day_weight_change,
    calculate_weekly_boxing_sessions,
    calculate_weekly_gym_sessions,
    calculate_weekly_run_distance,
    calculate_weight_change,
    get_latest_run_summary,
)
from utils.data_loader import (
    get_latest_weight,
    load_boxing_data,
    load_gym_data,
    load_runs_data,
    load_weight_data,
)
from utils.date_utils import get_greeting, get_today_label
from utils.quote_loader import get_quote_of_the_day
from utils.settings_loader import load_settings
from utils.style_loader import load_css


st.set_page_config(
    page_title="Boxing Journey 2026",
    layout="wide",
)

load_css("assets/styles.css")


# ============================================================
# HELPERS
# ============================================================

def image_to_base64(image_path: str) -> str:
    path = Path(image_path)

    if not path.exists():
        return ""

    return base64.b64encode(path.read_bytes()).decode()


def calculate_goal_progress(
    start_weight: float,
    current_weight: float,
    goal_weight: float,
) -> float:
    if start_weight == goal_weight:
        return 1.0 if current_weight <= goal_weight else 0.0

    progress = (start_weight - current_weight) / (start_weight - goal_weight)

    return max(0.0, min(progress, 1.0))


def calculate_next_milestone(
    current_weight: float,
    goal_weight: float,
) -> tuple[float, float]:
    if current_weight <= goal_weight:
        return goal_weight, 0.0

    next_milestone = float(int(current_weight))

    if next_milestone >= current_weight:
        next_milestone -= 1

    next_milestone = max(next_milestone, goal_weight)
    milestone_remaining = current_weight - next_milestone

    return next_milestone, milestone_remaining


# ============================================================
# ACHIEVEMENT RENDERING
# ============================================================

def render_achievement_badge(achievement: dict) -> str:
    unlocked = bool(achievement["unlocked"])
    locked_class = "" if unlocked else " locked"

    kind = escape(str(achievement["kind"]))
    name = escape(str(achievement["name"]))
    detail = escape(str(achievement["detail"]))

    return (
        f'<div class="home-achievement-badge{locked_class}">'
        f'<div class="home-achievement-kind">{kind}</div>'
        f'<div class="home-achievement-name">{name}</div>'
        f'<div class="home-achievement-detail">{detail}</div>'
        f'</div>'
    )


def achievement_popup_html(achievement: dict) -> str:
    name = escape(str(achievement["name"]))
    detail = escape(str(achievement["detail"]))

    return (
        f'<div class="achievement-popup">'
        f'<div class="achievement-popup-top">Achievement unlocked</div>'
        f'<div class="achievement-popup-title">{name}</div>'
        f'<div class="achievement-popup-detail">{detail}</div>'
        f'</div>'
    )


def render_achievement_dialog(achievements: list[dict]) -> None:
    unlocked_count = sum(1 for achievement in achievements if achievement["unlocked"])
    total_count = len(achievements)
    locked_count = total_count - unlocked_count

    st.markdown(
        (
            f'<div class="achievement-dialog-header">'
            f'<div class="achievement-dialog-eyebrow">ACHIEVEMENTS</div>'
            f'<div class="achievement-dialog-title">{unlocked_count}/{total_count} unlocked</div>'
            f'<div class="achievement-dialog-subtitle">'
            f'Unlocked: {unlocked_count} · Locked: {locked_count}. '
            f'Active badges can disappear again if the condition is no longer true. '
            f'Milestone badges stay unlocked as long as the data proves you reached them.'
            f'</div>'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )

    categories = ["General", "Weight", "Running", "Boxing", "Gym"]

    tab_labels = ["Overview"] + categories
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        unlocked_achievements = [
            achievement
            for achievement in achievements
            if achievement["unlocked"]
        ]

        locked_achievements = [
            achievement
            for achievement in achievements
            if not achievement["unlocked"]
        ]

        if unlocked_achievements:
            unlocked_html = "".join(
                render_achievement_badge(achievement)
                for achievement in unlocked_achievements
            )

            st.markdown(
                (
                    f'<div class="achievement-section">'
                    f'<div class="achievement-section-title">Unlocked badges</div>'
                    f'<div class="achievement-section-grid">{unlocked_html}</div>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )

        if locked_achievements:
            next_locked_html = "".join(
                render_achievement_badge(achievement)
                for achievement in locked_achievements[:8]
            )

            st.markdown(
                (
                    f'<div class="achievement-section">'
                    f'<div class="achievement-section-title">Next locked badges</div>'
                    f'<div class="achievement-section-grid">{next_locked_html}</div>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )

    for tab, category in zip(tabs[1:], categories):
        with tab:
            category_achievements = [
                achievement
                for achievement in achievements
                if achievement["category"] == category
            ]

            if not category_achievements:
                st.info(f"No {category.lower()} achievements found.")
                continue

            category_unlocked = sum(
                1 for achievement in category_achievements
                if achievement["unlocked"]
            )

            category_total = len(category_achievements)

            st.markdown(
                (
                    f'<div class="achievement-section">'
                    f'<div class="achievement-section-title">'
                    f'{category} · {category_unlocked}/{category_total} unlocked'
                    f'</div>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )

            sorted_achievements = sorted(
                category_achievements,
                key=lambda achievement: not achievement["unlocked"],
            )

            badges_html = "".join(
                render_achievement_badge(achievement)
                for achievement in sorted_achievements
            )

            st.markdown(
                (
                    f'<div class="achievement-section-grid">'
                    f'{badges_html}'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )


@st.dialog("Achievements", width="large")
def achievements_dialog(achievements: list[dict]) -> None:
    render_achievement_dialog(achievements)

    if st.button("Close", use_container_width=True):
        st.session_state.open_achievements = False
        st.query_params.clear()
        st.rerun()


def handle_new_achievement_popup(achievements: list[dict]) -> None:
    current_unlocked_ids = {
        achievement["id"]
        for achievement in achievements
        if achievement["unlocked"]
    }

    state_key = "previous_home_achievement_ids"

    if state_key not in st.session_state:
        st.session_state[state_key] = list(current_unlocked_ids)
        return

    previous_unlocked_ids = set(st.session_state[state_key])
    new_ids = current_unlocked_ids - previous_unlocked_ids

    if new_ids:
        new_achievement = next(
            achievement
            for achievement in achievements
            if achievement["id"] in new_ids
        )

        st.markdown(
            achievement_popup_html(new_achievement),
            unsafe_allow_html=True,
        )

    st.session_state[state_key] = list(current_unlocked_ids)


# ============================================================
# PAGE CSS
# ============================================================

st.markdown(
    """
<style>
.top-action-button {
    position: fixed;
    top: 28px;
    z-index: 9997;
    border: 1px solid rgba(201, 162, 39, 0.46);
    background:
        radial-gradient(circle at top left, rgba(201, 162, 39, 0.16), transparent 34%),
        rgba(8, 8, 8, 0.94);
    color: rgba(245, 245, 245, 0.92) !important;
    border-radius: 999px;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.8px;
    text-decoration: none !important;
    text-transform: uppercase;
    box-shadow:
        0 14px 36px rgba(0, 0, 0, 0.35),
        0 0 18px rgba(201, 162, 39, 0.12);
}

.top-action-button:visited {
    color: rgba(245, 245, 245, 0.92) !important;
}

.top-action-button:hover {
    color: #C9A227 !important;
    border-color: rgba(201, 162, 39, 0.78);
    box-shadow:
        0 16px 42px rgba(0, 0, 0, 0.42),
        0 0 24px rgba(201, 162, 39, 0.18);
}

.statistics-button {
    right: 170px;
}

.achievements-button {
    right: 48px;
}

.achievement-dialog-header {
    border: 1px solid rgba(201, 162, 39, 0.18);
    background:
        radial-gradient(circle at top left, rgba(201, 162, 39, 0.10), transparent 34%),
        rgba(255,255,255,0.035);
    border-radius: 20px;
    padding: 18px 20px;
    margin-bottom: 16px;
}

.achievement-dialog-eyebrow {
    color: rgba(201, 162, 39, 0.92);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.achievement-dialog-title {
    color: rgba(245,245,245,0.96);
    font-size: 28px;
    font-weight: 900;
    letter-spacing: -0.6px;
}

.achievement-dialog-subtitle {
    color: rgba(245,245,245,0.58);
    font-size: 13px;
    margin-top: 6px;
    line-height: 1.45;
}

.achievement-section {
    margin-top: 18px;
}

.achievement-section-title {
    color: rgba(201, 162, 39, 0.92);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.achievement-section-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.home-achievement-badge {
    border: 1px solid rgba(201, 162, 39, 0.30);
    background:
        radial-gradient(circle at top left, rgba(201, 162, 39, 0.12), transparent 35%),
        rgba(201, 162, 39, 0.055);
    border-radius: 16px;
    padding: 14px 15px;
    box-shadow:
        0 14px 32px rgba(0,0,0,0.18),
        inset 0 0 0 1px rgba(255,255,255,0.025);
}

.home-achievement-badge.locked {
    border-color: rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.025);
    box-shadow: none;
}

.home-achievement-kind {
    color: rgba(201, 162, 39, 0.92);
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 1.3px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.home-achievement-badge.locked .home-achievement-kind {
    color: rgba(245,245,245,0.28);
}

.home-achievement-name {
    color: rgba(245,245,245,0.94);
    font-size: 15px;
    font-weight: 850;
    letter-spacing: -0.1px;
}

.home-achievement-badge.locked .home-achievement-name {
    color: rgba(245,245,245,0.38);
}

.home-achievement-detail {
    color: rgba(245,245,245,0.56);
    font-size: 12px;
    margin-top: 5px;
    line-height: 1.35;
}

.home-achievement-badge.locked .home-achievement-detail {
    color: rgba(245,245,245,0.30);
}

.achievement-popup {
    position: fixed;
    right: 32px;
    top: 88px;
    z-index: 9999;
    min-width: 280px;
    max-width: 360px;
    border: 1px solid rgba(201, 162, 39, 0.45);
    background:
        radial-gradient(circle at top left, rgba(201, 162, 39, 0.18), transparent 36%),
        linear-gradient(145deg, rgba(18,18,18,0.98), rgba(6,6,6,0.98));
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow:
        0 24px 70px rgba(0, 0, 0, 0.55),
        0 0 26px rgba(201, 162, 39, 0.18),
        inset 0 0 0 1px rgba(255,255,255,0.035);
    animation: achievementPop 4.2s ease-in-out forwards;
}

.achievement-popup-top {
    color: rgba(201, 162, 39, 0.95);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.achievement-popup-title {
    color: rgba(245,245,245,0.96);
    font-size: 18px;
    font-weight: 900;
    letter-spacing: -0.25px;
}

.achievement-popup-detail {
    color: rgba(245,245,245,0.56);
    font-size: 13px;
    margin-top: 4px;
}

@keyframes achievementPop {
    0% {
        opacity: 0;
        transform: translateX(34px) translateY(8px) scale(0.96);
    }
    10% {
        opacity: 1;
        transform: translateX(0) translateY(0) scale(1);
    }
    78% {
        opacity: 1;
        transform: translateX(0) translateY(0) scale(1);
    }
    100% {
        opacity: 0;
        transform: translateX(34px) translateY(8px) scale(0.96);
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATA
# ============================================================

settings = load_settings()

user_name = settings["user_name"]
goal_weight = float(settings["goal_weight"])
start_weight = float(settings["start_weight"])

weight_df = load_weight_data()
runs_df = load_runs_data()
boxing_df = load_boxing_data()
gym_df = load_gym_data()

current_weight = get_latest_weight()
weight_value = f"{current_weight:.1f} kg"

weight_change = calculate_weight_change(weight_df)
last_7_day_weight_change = calculate_last_7_day_weight_change(weight_df)

last_7_day_run_distance = calculate_weekly_run_distance(runs_df)
last_7_day_boxing_sessions = calculate_weekly_boxing_sessions(boxing_df)
last_7_day_gym_sessions = calculate_weekly_gym_sessions(gym_df)

last_run_value, last_run_delta = get_latest_run_summary(runs_df)

boxing_count = int(last_7_day_boxing_sessions)
gym_count = int(last_7_day_gym_sessions)

boxing_card_value = (
    f"{boxing_count} session"
    if boxing_count == 1
    else f"{boxing_count} sessions"
)

gym_card_value = (
    f"{gym_count} workout"
    if gym_count == 1
    else f"{gym_count} workouts"
)

boxing_card_note = (
    "Last 7 days"
    if boxing_count > 0
    else "No session logged"
)

gym_card_note = (
    "Last 7 days"
    if gym_count > 0
    else "No session logged"
)

achievements = build_data_achievements(
    weight_df=weight_df,
    runs_df=runs_df,
    boxing_df=boxing_df,
    gym_df=gym_df,
    current_weight=current_weight,
    start_weight=start_weight,
    goal_weight=goal_weight,
)

if "open_achievements" not in st.session_state:
    st.session_state.open_achievements = False

if st.query_params.get("show_achievements") == "true":
    st.session_state.open_achievements = True
    st.query_params.clear()
    st.rerun()

if st.session_state.open_achievements:
    achievements_dialog(achievements)

quote, author = get_quote_of_the_day()
greeting = get_greeting(user_name)
today_label = get_today_label()

logo_base64 = image_to_base64("assets/logos/boxing_logo_premium.png")

progress = calculate_goal_progress(
    start_weight=start_weight,
    current_weight=current_weight,
    goal_weight=goal_weight,
)

progress_percent = progress * 100
remaining_kg = max(current_weight - goal_weight, 0.0)
next_milestone, milestone_remaining = calculate_next_milestone(
    current_weight=current_weight,
    goal_weight=goal_weight,
)


# ============================================================
# QUOTE SPLASH
# ============================================================

skip_splash = st.query_params.get("skip_splash") == "true"

if skip_splash:
    st.session_state.quote_splash_seen = True

if "quote_splash_seen" not in st.session_state:
    st.session_state.quote_splash_seen = False

show_quote_splash = not st.session_state.quote_splash_seen

if show_quote_splash:
    st.markdown(
        (
            f'<div class="quote-splash">'
            f'<div class="quote-splash-content">'
            f'<div class="quote-splash-text">❝ {quote} ❞</div>'
            f'<div class="quote-splash-author">— {author}</div>'
            f'</div>'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )

    st.session_state.quote_splash_seen = True

card_wait_class = ""
logo_wait_class = "splash-wait" if show_quote_splash else ""


# ============================================================
# PAGE
# ============================================================

st.markdown('<div class="dashboard-wrapper">', unsafe_allow_html=True)

handle_new_achievement_popup(achievements)


# ============================================================
# HERO
# ============================================================

countup_delay_ms = 4200 if show_quote_splash else 500

glove_trace_path = (
    "M 103.6 28.5 "
    "L 93.4 33.8 "
    "L 86.4 45.5 "
    "L 83.1 62.7 "
    "L 84.9 79.9 "
    "L 80.8 88.8 "
    "L 78.9 99.1 "
    "L 81.8 102.6 "
    "L 112.4 110.6 "
    "L 118.0 105.0 "
    "L 121.6 94.0 "
    "L 121.2 90.4 "
    "L 132.5 81.1 "
    "L 138.9 73.2 "
    "L 142.7 64.5 "
    "L 143.4 56.7 "
    "L 141.4 52.1 "
    "L 135.8 49.1 "
    "L 135.5 40.4 "
    "L 131.1 35.1 "
    "L 114.4 29.4 "
    "Z"
)

st.markdown(
    (
        f'<div class="hero-container">'
        f'<div class="hero-logo-wrap {logo_wait_class}">'
        f'<img class="hero-logo" src="data:image/png;base64,{logo_base64}" alt="Boxing Journey logo">'
        f'<svg class="hero-logo-trace" viewBox="0 0 220 147" aria-hidden="true">'
        f'<path class="hero-trace-path" d="{glove_trace_path}" pathLength="100" />'
        f'</svg>'
        f'</div>'
        f'<div>'
        f'<div class="hero-title">{APP_NAME} <span>{APP_YEAR}</span></div>'
        f'<div class="hero-subtitle">{greeting}</div>'
        f'<div class="hero-date">{today_label}</div>'
        f'</div>'
        f'</div>'
    ),
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)


# ============================================================
# SETTINGS + STATS + BADGES BUTTONS
# ============================================================

st.markdown(
    '<a class="settings-button" href="/settings" target="_self" title="Settings">⚙</a>',
    unsafe_allow_html=True,
)

st.markdown(
    '<a class="top-action-button statistics-button" href="/statistics" target="_self" title="Statistics">Stats</a>',
    unsafe_allow_html=True,
)

st.markdown(
    '<a class="top-action-button achievements-button" href="/?show_achievements=true" target="_self" title="Achievements">Badges</a>',
    unsafe_allow_html=True,
)


# ============================================================
# LAST 7 DAYS OVERVIEW
# ============================================================

weekly_overview(
    last_7_day_weight_change,
    last_7_day_run_distance,
    last_7_day_boxing_sessions,
    last_7_day_gym_sessions,
    animation_class=f"fade-in fade-delay-1 {card_wait_class}",
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# ============================================================
# MAIN CARDS
# ============================================================

col1, spacer1, col2 = st.columns([1, 0.06, 1])

with col1:
    metric_card(
        title="Weight",
        value=weight_value,
        delta=weight_change,
        page_url="/weight",
        animation_class=f"fade-in fade-delay-2 {card_wait_class}",
    )

with col2:
    metric_card(
        title="Run",
        value=last_run_value,
        delta=last_run_delta,
        page_url="/running",
        animation_class=f"fade-in fade-delay-2 {card_wait_class}",
    )

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col3, spacer2, col4 = st.columns([1, 0.06, 1])

with col3:
    metric_card(
        title="Boxing",
        value=boxing_card_value,
        delta=boxing_card_note,
        page_url="/boxing",
        animation_class=f"fade-in fade-delay-3 {card_wait_class}",
    )

with col4:
    metric_card(
        title="Gym",
        value=gym_card_value,
        delta=gym_card_note,
        page_url="/gym",
        animation_class=f"fade-in fade-delay-3 {card_wait_class}",
    )

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# ============================================================
# GOAL CARD
# ============================================================

st.markdown(
    (
        f'<div class="home-goal-card fade-in fade-delay-4 {card_wait_class}">'
        f'<div class="home-goal-eyebrow">GOAL PROGRESS</div>'
        f'<div class="home-goal-grid">'
        f'<div><div class="home-goal-label">Current</div><div class="home-goal-value">{current_weight:.1f} kg</div></div>'
        f'<div><div class="home-goal-label">Goal</div><div class="home-goal-value">{goal_weight:.1f} kg</div></div>'
        f'<div><div class="home-goal-label">Remaining</div><div class="home-goal-value">{remaining_kg:.1f} kg</div></div>'
        f'<div><div class="home-goal-label">Next milestone</div><div class="home-goal-value">{next_milestone:.1f} kg</div><div class="home-goal-muted">{milestone_remaining:.1f} kg away</div></div>'
        f'</div>'
        f'<div class="home-goal-progress-top">'
        f'<span>{progress_percent:.0f}% completed</span>'
        f'<span>{current_weight:.1f} kg → {goal_weight:.1f} kg</span>'
        f'</div>'
        f'<div class="home-goal-progress-track">'
        f'<div class="home-goal-progress-fill" style="width: {progress_percent:.0f}%;"></div>'
        f'</div>'
        f'</div>'
    ),
    unsafe_allow_html=True,
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# ============================================================
# QUOTE
# ============================================================

quote_card(
    quote,
    author,
    animation_class=f"fade-in fade-delay-5 {card_wait_class}",
)


# ============================================================
# COUNT-UP ANIMATION
# ============================================================

components.html(
    f"""
<script>
(function () {{
    function parseValue(text) {{
        const match = text.match(/-?\\d+(?:[.,]\\d+)?/);

        if (!match) {{
            return null;
        }}

        const numberText = match[0].replace(",", ".");
        const finalValue = parseFloat(numberText);

        if (Number.isNaN(finalValue)) {{
            return null;
        }}

        const decimals = numberText.includes(".")
            ? numberText.split(".")[1].length
            : 0;

        return {{
            finalValue: finalValue,
            decimals: decimals,
            prefix: text.slice(0, match.index),
            suffix: text.slice(match.index + match[0].length)
        }};
    }}

    function animateNumber(element) {{
        if (element.dataset.counted === "true") {{
            return;
        }}

        const originalText = element.dataset.final || element.textContent.trim();
        const parsed = parseValue(originalText);

        if (!parsed) {{
            return;
        }}

        element.dataset.counted = "true";

        const duration = 900;
        const startTime = performance.now();

        function easeOutCubic(t) {{
            return 1 - Math.pow(1 - t, 3);
        }}

        function frame(now) {{
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutCubic(progress);

            const currentValue = parsed.finalValue * easedProgress;
            const formattedValue = currentValue.toFixed(parsed.decimals);

            element.textContent = parsed.prefix + formattedValue + parsed.suffix;

            if (progress < 1) {{
                requestAnimationFrame(frame);
            }} else {{
                element.textContent = originalText;
            }}
        }}

        element.textContent =
            parsed.prefix +
            (0).toFixed(parsed.decimals) +
            parsed.suffix;

        requestAnimationFrame(frame);
    }}

    function runCountUp() {{
        const parentDocument = window.parent.document;
        const numbers = parentDocument.querySelectorAll(".count-up-number");
        numbers.forEach(animateNumber);
    }}

    setTimeout(runCountUp, {countup_delay_ms});
}})();
</script>
""",
    height=0,
)

st.markdown("</div>", unsafe_allow_html=True)