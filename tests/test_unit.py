from ai_agent import _clean_sql


"""
AI models often wrap SQL in Markdown code fences 
this test ensures those fences are removed before execution
"""
def test_clean_sql_strips_fences():
    raw = "```sql\nSELECT * FROM books;\n```"
    assert _clean_sql(raw) == "SELECT * FROM books;"


"""
ensures table names are normalized (case + pluralization)
to match actual database schema: books, users
"""
def test_clean_sql_normalizes_table_names():
    raw = "SELECT * FROM Books JOIN User ON Books.user_id = User.id"
    cleaned = _clean_sql(raw)

    # accepts either casing, since SQL itself is case-insensitive
    assert "FROM books" in cleaned or "from books" in cleaned
    assert "JOIN users" in cleaned or "join users" in cleaned


"""
ensures reading_status comparisons are made case-insensitive
by wrapping the column in LOWER()
"""
def test_clean_sql_normalized_reading_status():
    raw = "SELECT * FROM books WHERE reading_status = 'reading'"
    cleaned = _clean_sql(raw)
    assert "LOWER(reading_status) = 'reading'" in cleaned