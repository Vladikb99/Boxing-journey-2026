from __future__ import annotations

from html import escape

import streamlit as st


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
                1
                for achievement in category_achievements
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