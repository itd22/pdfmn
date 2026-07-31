import importlib

import pytest

from pdfpz.core.class_book_manifest import PdfManifestEntry
from pdftui.tui import (
    TuiSession,
    _action_save_as_db,
    _action_save_as_json,
    _action_save_as_yaml,
)


def _entry(name):
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.name = name
    return e


def _session_with_entries(policy, **kwargs):
    session = TuiSession(policy=policy, **kwargs)
    session.lib = session.get_lib()
    session.lib.entries = [_entry("a"), _entry("b")]
    return session


def test_save_as_json_works_regardless_of_current_policy(tmp_path):
    out = tmp_path / "out.json"
    # policy is "db", but Save as JSON should still work
    session = _session_with_entries("db", merged_json=str(out))

    _action_save_as_json(None, session)

    from pdftui.json_bridge import load
    assert sorted(e.name for e in load(str(out))) == ["a", "b"]
    assert "independent of current policy" in session.last_message


def test_save_as_yaml_works_regardless_of_current_policy(tmp_path):
    out = tmp_path / "out.yaml"
    session = _session_with_entries("json", saved_yaml=str(out), yaml_input_path="/x")

    _action_save_as_yaml(None, session)

    from pdftui.yaml_bridge import load
    assert sorted(e.name for e in load(str(out))) == ["a", "b"]


def test_save_as_db_works_regardless_of_current_policy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import pdftui.db_bridge as db_bridge_module
    import pdftui.db_schema as db_schema_module
    import pdftui.tui as tui_module

    importlib.reload(db_schema_module)
    importlib.reload(db_bridge_module)
    importlib.reload(tui_module)

    session = tui_module.TuiSession(policy="json")
    session.lib = session.get_lib()
    session.lib.entries = [_entry("a"), _entry("b")]

    tui_module._action_save_as_db(None, session)

    assert db_bridge_module.is_exist() is True
    assert sorted(e.name for e in db_bridge_module.load_all()) == ["a", "b"]


def test_save_as_json_with_no_entries_gives_friendly_message():
    session = TuiSession(policy="json")
    _action_save_as_json(None, session)
    assert "Nothing to save" in session.last_message
