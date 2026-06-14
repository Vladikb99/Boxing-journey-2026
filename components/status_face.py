def status_face_html(status: str) -> str:
    valid_statuses = {"happy", "medium", "sad"}

    if status not in valid_statuses:
        status = "medium"

    return f"""
<div class="status-face-wrap">
<div class="status-face status-face-{status}">
<div class="status-face-eye status-face-eye-left"></div>
<div class="status-face-eye status-face-eye-right"></div>
<div class="status-face-mouth"></div>
</div>
</div>
"""