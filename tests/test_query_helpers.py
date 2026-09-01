from src.sql_utils import escape_literal, quote_identifier


def test_quote_identifier_escapes_quotes():
    assert quote_identifier('a\"b') == '"a""b"'


def test_escape_literal_escapes_single_quote():
    assert escape_literal("a'b") == "a''b"


def test_catalog_skips_nested_dataset_container(tmp_path):
    from src.catalog import discover_tables

    nested = tmp_path / tmp_path.name
    nested.mkdir()
    (nested / "part-00000").write_bytes(b"ORC")

    revision = tmp_path / "revision"
    revision.mkdir()
    (revision / "part-00000").write_bytes(b"ORC")

    names = {table.name for table in discover_tables(tmp_path)}
    assert "revision" in names
    assert tmp_path.name not in names
