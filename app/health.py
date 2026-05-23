from __future__ import annotations

from sqlalchemy import text

from app.database.session import SessionLocal, init_db


def check() -> None:
    init_db()
    with SessionLocal() as session:
        session.execute(text("select 1"))


if __name__ == "__main__":
    check()
