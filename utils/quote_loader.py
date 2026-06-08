from datetime import date
from pathlib import Path


def load_quotes(file_path: str = "data/quotes.txt") -> list[tuple[str, str]]:
    quotes_path = Path(file_path)

    if not quotes_path.exists():
        return [("Discipline beats motivation.", "Unknown")]

    quotes = []

    with open(quotes_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or "|" not in line:
                continue

            quote, author = line.split("|", maxsplit=1)
            quotes.append((quote.strip(), author.strip()))

    return quotes or [("Discipline beats motivation.", "Unknown")]


def get_quote_of_the_day() -> tuple[str, str]:
    quotes = load_quotes()
    day_number = date.today().toordinal()
    quote_index = day_number % len(quotes)

    return quotes[quote_index]