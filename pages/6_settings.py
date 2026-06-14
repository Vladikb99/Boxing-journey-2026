from html import escape as html_escape

import streamlit as st

from components.home_button import home_button
from components.page_header import page_header
from utils.export_tools import (
    create_ai_review_export_zip,
    create_ai_review_summary,
    create_data_health_report_text,
    create_full_backup_zip,
    get_data_health_check,
)
from utils.settings_loader import load_settings, save_settings
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Settings", eyebrow="APP SETTINGS")
home_button()


def _safe_text(value: object) -> str:
    if value is None:
        return "-"

    text = str(value)

    if text.strip() == "" or text.lower() == "nan":
        return "-"

    return html_escape(text)


def _status_class(status: object) -> str:
    status_text = str(status).strip().lower()

    if status_text == "ok":
        return "ok"

    if status_text == "warning":
        return "warning"

    if status_text in ["missing", "error", "empty"]:
        return "bad"

    return "neutral"


def _section_card(eyebrow: str, title: str, subtitle: str) -> str:
    return f"""
<div class="settings-section-card soft-appear">
    <div class="settings-section-eyebrow">{html_escape(eyebrow)}</div>
    <div class="settings-section-title">{html_escape(title)}</div>
    <div class="settings-section-subtitle">{html_escape(subtitle)}</div>
</div>
"""


def _health_summary_html(health_df) -> str:
    status_counts = health_df["status"].value_counts().to_dict()

    ok_count = int(status_counts.get("OK", 0))
    warning_count = int(status_counts.get("Warning", 0))
    missing_count = int(status_counts.get("Missing", 0))
    error_count = int(
        status_counts.get("Error", 0)
        + status_counts.get("Empty", 0)
    )

    total_issues = warning_count + missing_count + error_count
    system_status = "Clean" if total_issues == 0 else "Review"
    system_class = "ok" if total_issues == 0 else "warning"

    return f"""
<div class="settings-health-grid soft-appear">
    <div class="settings-health-card health-ok">
        <div class="settings-health-label">OK FILES</div>
        <div class="settings-health-value">{ok_count}</div>
        <div class="settings-health-detail">Readable files</div>
    </div>
    <div class="settings-health-card health-warning">
        <div class="settings-health-label">WARNINGS</div>
        <div class="settings-health-value">{warning_count}</div>
        <div class="settings-health-detail">Needs review</div>
    </div>
    <div class="settings-health-card health-bad">
        <div class="settings-health-label">MISSING</div>
        <div class="settings-health-value">{missing_count}</div>
        <div class="settings-health-detail">Files not found</div>
    </div>
    <div class="settings-health-card health-{system_class}">
        <div class="settings-health-label">SYSTEM</div>
        <div class="settings-health-value">{system_status}</div>
        <div class="settings-health-detail">Errors / empty: {error_count}</div>
    </div>
</div>
"""


def _health_file_list_html(health_df) -> str:
    rows = []

    for _, row in health_df.iterrows():
        file_name = _safe_text(row.get("file", "-"))
        status = _safe_text(row.get("status", "-"))
        status_class = _status_class(row.get("status", ""))
        row_count = _safe_text(row.get("rows", "-"))
        last_date = _safe_text(row.get("last_date", "-"))
        size_kb = _safe_text(row.get("size_kb", "-"))
        notes = _safe_text(row.get("notes", "-"))

        rows.append(
            f'<div class="settings-file-row">'
            f'<div>'
            f'<div class="settings-file-name">{file_name}</div>'
            f'<div class="settings-file-note">{notes}</div>'
            f'</div>'
            f'<div class="settings-file-stat">'
            f'<span>Rows</span>'
            f'<strong>{row_count}</strong>'
            f'</div>'
            f'<div class="settings-file-stat">'
            f'<span>Last date</span>'
            f'<strong>{last_date}</strong>'
            f'</div>'
            f'<div class="settings-file-stat">'
            f'<span>Size</span>'
            f'<strong>{size_kb} KB</strong>'
            f'</div>'
            f'<div class="settings-status-pill {status_class}">{status}</div>'
            f'</div>'
        )

    return (
        f'<div class="settings-file-list soft-appear">'
        f'{"".join(rows)}'
        f'</div>'
    )


st.markdown('<div class="page-wrapper settings-page">', unsafe_allow_html=True)

settings = load_settings()

# ============================================================
# PERSONAL SETUP
# ============================================================

st.markdown(
    _section_card(
        eyebrow="USER PARAMETERS",
        title="Personal setup",
        subtitle="Change the values used across the dashboard.",
    ),
    unsafe_allow_html=True,
)

st.markdown('<div class="settings-form-shell">', unsafe_allow_html=True)

with st.form("settings_form"):
    user_name = st.text_input(
        "User name",
        value=settings.get("user_name", "Vladik"),
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        height_m = st.number_input(
            "Height (m)",
            min_value=1.20,
            max_value=2.30,
            value=float(settings.get("height_m", 1.84)),
            step=0.01,
        )

    with col2:
        start_weight = st.number_input(
            "Start weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=float(settings.get("start_weight", 86.7)),
            step=0.1,
        )

    with col3:
        goal_weight = st.number_input(
            "Goal weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=float(settings.get("goal_weight", 75.0)),
            step=0.1,
        )

    submitted = st.form_submit_button(
        "Save settings",
        use_container_width=True,
    )

    if submitted:
        new_settings = {
            "user_name": user_name.strip() or "User",
            "height_m": height_m,
            "start_weight": start_weight,
            "goal_weight": goal_weight,
        }

        save_settings(new_settings)

        st.success("Settings saved.")
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# DATA HEALTH CHECK
# ============================================================

st.markdown(
    _section_card(
        eyebrow="DATA CHECK",
        title="Data health",
        subtitle="Quick check of your training files before backup, export, or later restore.",
    ),
    unsafe_allow_html=True,
)

health_df = get_data_health_check()

if health_df.empty:
    st.warning("No data health information found.")
else:
    st.markdown(_health_summary_html(health_df), unsafe_allow_html=True)
    st.markdown(_health_file_list_html(health_df), unsafe_allow_html=True)

    with st.expander("Technical data health table"):
        display_health_df = health_df.copy()
        display_health_df = display_health_df.drop(columns=["exists"], errors="ignore")

        st.dataframe(
            display_health_df,
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Full data health report"):
        st.text(create_data_health_report_text())

# ============================================================
# BACKUP AND EXPORT
# ============================================================

st.markdown(
    _section_card(
        eyebrow="DATA SAFETY",
        title="Backup & export",
        subtitle="Use backup for safety. Use AI review export when you want weekly coaching comments.",
    ),
    unsafe_allow_html=True,
)

review_days = st.selectbox(
    "AI review period",
    options=[7, 14, 30],
    index=0,
    format_func=lambda days: f"Last {days} days",
)

st.markdown('<div class="settings-export-section">', unsafe_allow_html=True)

backup_col, review_col = st.columns(2)

with backup_col:
    st.markdown(
        """
<div class="settings-export-card">
    <div class="settings-export-eyebrow">FULL BACKUP</div>
    <div class="settings-export-title">Protect your data</div>
    <div class="settings-export-copy">
        Downloads your CSV files, settings, quotes, backup manifest, and health report.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    backup_filename, backup_bytes = create_full_backup_zip()

    st.download_button(
        label="Download full backup",
        data=backup_bytes,
        file_name=backup_filename,
        mime="application/zip",
        use_container_width=True,
    )

with review_col:
    st.markdown(
        f"""
<div class="settings-export-card">
    <div class="settings-export-eyebrow">AI REVIEW</div>
    <div class="settings-export-title">Send weekly progress</div>
    <div class="settings-export-copy">
        Creates a {review_days}-day coaching export with files, health report, and readable summary.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    review_filename, review_bytes = create_ai_review_export_zip(days=review_days)

    st.download_button(
        label="Download AI review export",
        data=review_bytes,
        file_name=review_filename,
        mime="application/zip",
        use_container_width=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Preview AI review summary"):
    st.text(create_ai_review_summary(days=review_days))

st.markdown("</div>", unsafe_allow_html=True)