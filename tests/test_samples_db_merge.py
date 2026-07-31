import importlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"
SAMPLES2_DIR = PROJECT_ROOT / "samples2"


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Fresh db_bridge module bound to an isolated books_db.sqlite per test."""
    monkeypatch.chdir(tmp_path)
    from pdftui import db_bridge as db_bridge_module
    from pdftui import db_schema as db_schema_module

    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)
    return db_bridge_module


def test_db_created_from_samples_then_merged_with_samples2(db):
    from pdftui.crawl import PdfCrawler

    # 1. Build the db from samples/
    db.create_db()
    samples_entries = PdfCrawler(str(SAMPLES_DIR)).crawl()
    added_first = db.merge_to_db(samples_entries)

    assert added_first == 3  # dummy-book-one, dummy-book-two, dummy-book-three
    assert sorted(e.name for e in db.load_all()) == [
        "dummy-book-one",
        "dummy-book-three",
        "dummy-book-two",
    ]

    # 2. Crawl samples2/ (same one/three, missing two, plus new four) and merge
    samples2_entries = PdfCrawler(str(SAMPLES2_DIR)).crawl()
    added_second = db.merge_to_db(samples2_entries)

    # only "dummy-book-four" is genuinely new by name
    assert added_second == 1

    final_names = sorted(e.name for e in db.load_all())
    assert final_names == [
        "dummy-book-four",
        "dummy-book-one",
        "dummy-book-three",
        "dummy-book-two",
    ]


def test_merge_key_is_name_not_path(db):
    """Same filename in a different directory is treated as the same book;
    input_file still records the original path it was first seen at."""
    from pdftui.crawl import PdfCrawler

    db.create_db()
    db.merge_to_db(PdfCrawler(str(SAMPLES_DIR)).crawl())
    db.merge_to_db(PdfCrawler(str(SAMPLES2_DIR)).crawl())

    entries = {e.name: e for e in db.load_all()}

    # dummy-book-one exists in both dirs -> kept only once, from samples/ (first write wins)
    assert str(SAMPLES_DIR) in entries["dummy-book-one"].input_file
    assert str(SAMPLES2_DIR) not in entries["dummy-book-one"].input_file

    # dummy-book-three: same story, nested under subfolder/ in both dirs
    assert str(SAMPLES_DIR) in entries["dummy-book-three"].input_file
    assert entries["dummy-book-three"].file == "subfolder/dummy-book-three.pdf"

    # dummy-book-four only exists in samples2/ -> its path is recorded there
    assert str(SAMPLES2_DIR) in entries["dummy-book-four"].input_file

    # dummy-book-two only exists in samples/
    assert str(SAMPLES_DIR) in entries["dummy-book-two"].input_file
