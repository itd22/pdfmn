import json

from pdfmanifest.tui import SETTINGS_FIELDS, TuiSession, load_saved_settings, save_saved_settings


def test_load_saved_settings_missing_file_returns_empty(tmp_path):
    assert load_saved_settings(str(tmp_path / "nope.json")) == {}


def test_save_then_load_round_trip(tmp_path):
    p = tmp_path / "settings.json"
    session = TuiSession(
        policy="yaml",
        top_dir="my-pdfs",
        main_json="m.json",
        merged_json="merged2.json",
        main_yaml="m.yaml",
        saved_yaml="saved2.yaml",
        yaml_input_path="/x",
    )
    save_saved_settings(session, str(p))

    loaded = load_saved_settings(str(p))
    assert loaded == {
        "policy": "yaml",
        "top_dir": "my-pdfs",
        "main_json": "m.json",
        "merged_json": "merged2.json",
        "main_yaml": "m.yaml",
        "saved_yaml": "saved2.yaml",
        "yaml_input_path": "/x",
    }


def test_save_writes_only_settings_fields_on_disk(tmp_path):
    p = tmp_path / "settings.json"
    session = TuiSession()
    save_saved_settings(session, str(p))
    raw = json.loads(p.read_text())
    assert set(raw.keys()) == set(SETTINGS_FIELDS)


def test_load_ignores_unknown_keys_and_corrupt_file(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{"policy": "db", "unrelated": "ignored"}')
    loaded = load_saved_settings(str(p))
    assert loaded == {"policy": "db"}

    p.write_text("not valid json {{{")
    assert load_saved_settings(str(p)) == {}
