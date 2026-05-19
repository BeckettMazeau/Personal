import pytest

from app.core.utils import clean_and_parse_json


@pytest.mark.parametrize(
    "content,expected",
    [
        ('{"a": 1}', {"a": 1}),
        ('```json\n{"a": 1}\n```', {"a": 1}),
        ('```JSON\n{"a": 1}\n```', {"a": 1}),
        ('```\n{"a": 1}\n```', {"a": 1}),
        ('Here is the JSON: {"a": 1}', {"a": 1}),
        ('{"a": 1}\nThanks!', {"a": 1}),
        ('Sure! ```json\n[{"id": 0, "delete": true}]\n```', [{"id": 0, "delete": True}]),
        ('[{"x": 1}, {"x": 2}]', [{"x": 1}, {"x": 2}]),
    ],
)
def test_clean_and_parse_json_variants(content, expected):
    assert clean_and_parse_json(content) == expected


def test_clean_and_parse_json_none_inputs():
    assert clean_and_parse_json(None) is None
    assert clean_and_parse_json("") is None


def test_clean_and_parse_json_hard_failure():
    assert clean_and_parse_json("totally not json at all") is None


def test_clean_and_parse_json_nested_braces():
    content = 'Output: {"outer": {"inner": [1, 2, 3]}, "k": "v"}'
    assert clean_and_parse_json(content) == {"outer": {"inner": [1, 2, 3]}, "k": "v"}


def test_clean_and_parse_json_string_with_braces():
    content = '{"msg": "hello {world}"}'
    assert clean_and_parse_json(content) == {"msg": "hello {world}"}
