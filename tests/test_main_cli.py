from click.testing import CliRunner

from pdfmanifest.main import main


def test_tui_defaults_to_yes_in_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--tui" in result.output
    assert "yes|no" in result.output
    assert "default" in result.output.lower()


def test_tui_no_requires_action():
    runner = CliRunner()
    result = runner.invoke(main, ["--tui=no"])
    assert result.exit_code != 0
    assert "--action is required" in result.output


def test_tui_no_crawl_action_requires_top_dir(tmp_path):
    runner = CliRunner()
    main_json = tmp_path / "main.json"
    main_json.write_text("[]")
    result = runner.invoke(
        main, ["--tui=no", "--action", "crawl_to_json", "--main-json", str(main_json)]
    )
    assert result.exit_code != 0
    assert "--top-dir is required" in result.output


def test_tui_no_load_json_runs_classic_cli(tmp_path):
    runner = CliRunner()
    main_json = tmp_path / "main.json"
    main_json.write_text(
        '[{"valid_pdf": true, "input_file": "", "file": "a.pdf", "title": "", '
        '"author": "", "size": 0, "Optimized": false, "isbn": "", "name": "a", '
        '"year": "", "isbn_normalized": "", "book_id": "", "book_type": "pdf"}]'
    )
    result = runner.invoke(
        main, ["--tui=no", "--action", "load_json", "--main-json", str(main_json)]
    )
    assert result.exit_code == 0
    assert "a" in result.output.splitlines()


def test_tui_yes_passes_main_json_and_main_yaml_to_run_tui(monkeypatch, tmp_path):
    """Regression test: --main-json / --main-yaml must reach run_tui() so
    Settings starts from the paths the user gave on the command line."""
    captured = {}

    def fake_run_tui(**kwargs):
        captured.update(kwargs)

    import pdfmanifest.tui as tui_module
    monkeypatch.setattr(tui_module, "run_tui", fake_run_tui)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--tui=yes",
            "--main-json", "custom_main.json",
            "--main-yaml", "custom_main.yaml",
        ],
    )
    assert result.exit_code == 0
    assert captured.get("main_json") == "custom_main.json"
    assert captured.get("main_yaml") == "custom_main.yaml"
