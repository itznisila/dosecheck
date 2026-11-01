import json
import shutil
from pathlib import Path

import pytest

import server

SAMPLE = Path(__file__).parent.parent / "data" / "mom.sample.json"


@pytest.fixture(autouse=True)
def fresh_data(tmp_path, monkeypatch):
    """Give every test its own copy of the sample data."""
    copy = tmp_path / "mom.json"
    shutil.copy(SAMPLE, copy)
    monkeypatch.setattr(server, "DATA", copy)
    return copy


def test_list_people():
    assert "Mom" in server.list_people()


def test_whats_due_lists_two_morning_pills():
    text = server.whats_due("Mom")
    assert "Mom still needs 2" in text
    assert "blood pressure pill" in text
    assert "vitamin D" in text
    assert "statin|evening|not due yet" in text


def test_whats_due_unknown_person():
    assert "only have a schedule for Mom" in server.whats_due("Dad")


def test_mark_taken_updates_saved_data(fresh_data):
    text = server.mark_taken("Mom", "blood pressure pill")
    assert "Marked Mom's blood pressure pill as taken" in text
    saved = json.loads(fresh_data.read_text())
    bp = next(m for m in saved["meds"] if m["id"] == "blood-pressure")
    assert bp["taken"] is True


def test_mark_taken_accepts_aliases():
    assert "Marked" in server.mark_taken("Mom", "lisinopril")


def test_mark_taken_twice_is_safe():
    server.mark_taken("Mom", "vitamin D")
    assert "already marked taken" in server.mark_taken("Mom", "vitamin D")


def test_mark_taken_refuses_pill_not_due_yet(fresh_data):
    text = server.mark_taken("Mom", "statin")
    assert "not due yet" in text
    saved = json.loads(fresh_data.read_text())
    statin = next(m for m in saved["meds"] if m["id"] == "statin")
    assert statin["taken"] is False


def test_mark_taken_unknown_pill():
    assert "could not find that pill" in server.mark_taken("Mom", "aspirin")


def test_nothing_due_after_both_morning_pills():
    server.mark_taken("Mom", "blood pressure")
    text = server.mark_taken("Mom", "vitamin D")
    assert "Nothing else is due right now" in text
    assert "nothing due right now" in server.whats_due("Mom")


def test_todays_summary():
    server.mark_taken("Mom", "bp")
    text = server.todays_summary("Mom")
    assert "blood pressure pill (morning): taken" in text
    assert "vitamin D (morning): due now" in text
    assert "statin (evening): not due yet" in text
