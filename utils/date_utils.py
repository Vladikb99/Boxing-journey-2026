from datetime import datetime


def get_greeting(name: str = "Vladik") -> str:
    current_hour = datetime.now().hour

    if current_hour < 12:
        return f"Good morning, {name}."

    if current_hour < 18:
        return f"Good afternoon, {name}."

    return f"Good evening, {name}."


def get_today_label() -> str:
    return datetime.now().strftime("%A • %d %B %Y")