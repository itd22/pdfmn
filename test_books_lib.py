import importlib

import pytest

from books_lib import BooksLib
from json_bridge import save as json_save
from manifest import PdfManifestEntry


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

    lib = BooksLib(policy="json", json_path=str(main_json))
    lib.load()

    assert [e.name for e in lib.entries] == ["a"]


def test_json_policy_crawl_and_merge_and_save(tmp_path):
    main_json = tmp_path / "main.json"
    merged_json = tmp_path / "merged.json"
    json_save(str(main_json), [_entry("a")])
    pdf_dir = _make_pdf_dir(tmp_path, "a", "b")

    lib = BooksLib(policy="json", json_path=str(main_json), merged_json_path=str(merged_json))
    lib.load()
    lib.crawl_and_merge(str(pdf_dir))
    lib.save()

    assert sorted(e.name for e in lib.entries) == ["a", "b"]
    assert merged_json.exists()

    from json_bridge import load as json_load
    reloaded = json_load(str(merged_json))
    assert sorted(e.name for e in reloaded) == ["a", "b"]


def test_db_policy_load_creates_db_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import db_bridge as db_bridge_module
    import db_schema as db_schema_module
    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)

    lib = BooksLib(policy="db")
    lib.load()

    assert db_bridge_module.is_exist() is True
    assert lib.entries == []


def test_db_policy_crawl_and_merge(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import db_bridge as db_bridge_module
    import db_schema as db_schema_module
    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)

    pdf_dir = _make_pdf_dir(tmp_path, "a", "b")

    lib = BooksLib(policy="db")
    lib.load()
    lib.crawl_and_merge(str(pdf_dir))

    assert sorted(e.name for e in lib.entries) == ["a", "b"]
    assert sorted(e.name for e in db_bridge_module.load_all()) == ["a", "b"]


def test_invalid_policy_raises():
    with pytest.raises(ValueError):
        BooksLib(policy="xml")
