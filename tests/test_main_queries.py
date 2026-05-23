from datetime import date

from app.main import _build_queries


def test_build_queries_combines_keywords_and_departments():
    queries = _build_queries(["solar", "panel solar"], ["Tacna", "Cusco"], date(2026, 5, 22))

    assert [(query.keyword, query.department) for query in queries] == [
        ("solar", "TACNA"),
        ("solar", "CUSCO"),
        ("panel solar", "TACNA"),
        ("panel solar", "CUSCO"),
    ]


def test_build_queries_uses_all_departments_when_empty():
    queries = _build_queries(["solar"], [], date(2026, 5, 22))

    assert len(queries) == 1
    assert queries[0].department is None
