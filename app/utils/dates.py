from __future__ import annotations

from datetime import date, datetime


def parse_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def days_until(value: date | None, today: date | None = None) -> int | None:
    if value is None:
        return None
    today = today or date.today()
    return (value - today).days
