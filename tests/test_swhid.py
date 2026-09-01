import pytest

from src.swhid import parse_swhid


def test_parse_revision_swhid():
    value = "swh:1:rev:0123456789abcdef0123456789abcdef01234567"
    parsed = parse_swhid(value)
    assert parsed.version == 1
    assert parsed.object_type == "rev"
    assert parsed.table == "revision"
    assert parsed.object_id == "0123456789abcdef0123456789abcdef01234567"


def test_parse_qualified_swhid():
    value = "swh:1:dir:0123456789abcdef0123456789abcdef01234567;lines=1-2"
    parsed = parse_swhid(value)
    assert parsed.qualifiers == ";lines=1-2"


def test_reject_invalid_swhid():
    with pytest.raises(ValueError):
        parse_swhid("not-a-swhid")
