import json

from pdfpz.core.class_book_manifest import PdfManifestEntry
from pdftui.json_bridge import is_exist, load, save


def test_load_missing_file_returns_empty_list(tmp_path):
    assert load(str(tmp_path / "nope.json")) == []


def test_is_exist(tmp_path):
    p = tmp_path / "main.json"
    assert is_exist(str(p)) is False
    p.write_text("[]")
    assert is_exist(str(p)) is True


def test_save_then_load_round_trip(tmp_path):
    p = tmp_path / "main.json"
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.name = "a"
    e.title = "Title A"
    e.optimized = True

    save(str(p), [e])
    loaded = load(str(p))

    assert len(loaded) == 1
    assert loaded[0].name == "a"
    assert loaded[0].title == "Title A"
    assert loaded[0].optimized is True


def test_save_uses_capitalized_optimized_key_on_disk(tmp_path):
    p = tmp_path / "main.json"
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.name = "a"
    e.optimized = True
    save(str(p), [e])

    raw = json.loads(p.read_text())
    assert raw[0]["Optimized"] is True
    assert "optimized" not in raw[0]
