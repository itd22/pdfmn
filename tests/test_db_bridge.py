import importlib

import pytest

from pdfpz.core.class_book_manifest import PdfManifestEntry


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Fresh db_bridge module bound to an isolated books_db.sqlite per test."""
    monkeypatch.chdir(tmp_path)
    from pdftui import db_bridge as db_bridge_module
    from pdftui import db_schema as db_schema_module

    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)
    return db_bridge_module


def _entry(name, **overrides):
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.name = name
    for k, v in overrides.items():
        setattr(e, k, v)
    return e


def test_is_exist_false_before_create(db):
    assert db.is_exist() is False


def test_create_db_creates_file(db):
    db.create_db()
    assert db.is_exist() is True


def test_merge_to_db_adds_only_new_names(db):
    db.create_db()
    added1 = db.merge_to_db([_entry("a"), _entry("b")])
    assert added1 == 2

    added2 = db.merge_to_db([_entry("a"), _entry("c")])
    assert added2 == 1

    names = sorted(e.name for e in db.load_all())
    assert names == ["a", "b", "c"]


def test_merge_to_db_dedupes_within_batch(db):
    db.create_db()
    added = db.merge_to_db([_entry("a"), _entry("a")])
    assert added == 1
    assert len(db.load_all()) == 1


def test_load_all_round_trips_fields(db):
    db.create_db()
    db.merge_to_db([_entry("a", title="Title A", optimized=True, size=42)])
    loaded = db.load_all()
    assert len(loaded) == 1
    assert loaded[0].title == "Title A"
    assert loaded[0].optimized is True
    assert loaded[0].size == 42
