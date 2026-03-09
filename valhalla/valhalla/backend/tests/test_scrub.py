import json

from app.observability.scrub import REPL, scrub_any, scrub_headers, scrub_json_text_maybe


def test_scrub_headers():
    h = {"Authorization": "Bearer abcdefghijklmnop", "x-api-key": "xyz", "User-Agent": "UA/1.0"}
    s = scrub_headers(h)
    assert s["Authorization"] == REPL
    assert s["x-api-key"] == REPL
    assert "UA/1.0" in s["User-Agent"]


def test_scrub_any_mapping_and_text():
    obj = {"password": "p@ss", "note": "email foo@bar.com and card 4242 4242 4242 4242"}
    s = scrub_any(obj)
    assert s["password"] == REPL
    assert REPL in s["note"]


def test_scrub_json_text_maybe():
    txt = json.dumps({"token": "abcdEFGHijkl-1234", "nested": {"email": "a@b.co"}})
    out = scrub_json_text_maybe(txt)
    assert REPL in out
