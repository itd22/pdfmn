import importlib

import pytest

from pdftui.books_lib import BooksSpine
from pdftui.json_bridge import save as json_save
from pdfpz.core.class_book_manifest import PdfManifestEntry
from pdftui.yaml_bridge import save as yaml_save


def _entry(name, **overrides):
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.name = name
    for k, v in overrides.items():
        setattr(e, k, v)
    return e


def _make_pdf_dir(tmp_path, *names):
    d = tmp_path / "books"
    d.mkdir()
    for n in names:
        (d / f"{n}.pdf").write_text("")
    return d


def test_json_policy_load(tmp_path):
    main_json = tmp_path / "main.json"
    json_save(str(main_json), [_entry("a")])

    lib = BooksSpine(policy="json", json_path=str(main_json))
    lib.load()

    assert [e.name for e in lib.shelf.books] == ["a"]


def test_json_policy_crawl_and_merge_and_save(tmp_path):
    main_json = tmp_path / "main.json"
    merged_json = tmp_path / "merged.json"
    json_save(str(main_json), [_entry("a")])
    pdf_dir = _make_pdf_dir(tmp_path, "a", "b")

    lib = BooksSpine(policy="json", json_path=str(main_json), merged_json_path=str(merged_json))
    lib.load()
    lib.crawl_and_merge(str(pdf_dir))
    lib.save()

    assert sorted(e.name for e in lib.shelf.books) == ["a", "b"]
    assert merged_json.exists()

    from pdftui.json_bridge import load as json_load
    reloaded = json_load(str(merged_json))
    assert sorted(e.name for e in reloaded) == ["a", "b"]


def test_db_policy_load_creates_db_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from pdftui import db_bridge as db_bridge_module
    from pdftui import db_schema as db_schema_module
    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)

    lib = BooksSpine(policy="db")
    lib.load()

    assert db_bridge_module.is_exist() is True
    assert lib.shelf.books == []


def test_db_policy_crawl_and_merge(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from pdftui import db_bridge as db_bridge_module
    from pdftui import db_schema as db_schema_module
    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)

    pdf_dir = _make_pdf_dir(tmp_path, "a", "b")

    lib = BooksSpine(policy="db")
    lib.load()
    lib.crawl_and_merge(str(pdf_dir))

    assert sorted(e.name for e in lib.shelf.books) == ["a", "b"]
    assert sorted(e.name for e in db_bridge_module.load_all()) == ["a", "b"]


def test_yaml_policy_load(tmp_path):
    main_yaml = tmp_path / "main.yaml"
    yaml_save("/some/input", [_entry("a")], str(main_yaml))

    lib = BooksSpine(policy="yaml", yaml_path=str(main_yaml))
    lib.load()

    assert [e.name for e in lib.shelf.books] == ["a"]


def test_yaml_policy_crawl_and_merge_and_save(tmp_path):
    main_yaml = tmp_path / "main.yaml"
    saved_yaml = tmp_path / "saved.yaml"
    yaml_save("/some/input", [_entry("a")], str(main_yaml))
    pdf_dir = _make_pdf_dir(tmp_path, "a", "b")

    lib = BooksSpine(
        policy="yaml",
        yaml_path=str(main_yaml),
        saved_yaml_path=str(saved_yaml),
        yaml_input_path=str(pdf_dir),
    )
    lib.load()
    lib.crawl_and_merge(str(pdf_dir))
    lib.save()

    assert sorted(e.name for e in lib.shelf.books) == ["a", "b"]
    assert saved_yaml.exists()

    from pdftui.yaml_bridge import load as yaml_load
    reloaded = yaml_load(str(saved_yaml))
    assert sorted(e.name for e in reloaded) == ["a", "b"]


def test_invalid_policy_raises():
    with pytest.raises(ValueError):
        BooksSpine(policy="xml")
