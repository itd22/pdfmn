# pipx packaging

## What changed and why

The old `src/*.py` layout was flat modules with no package boundary. That
worked for `pytest` (via `pythonpath = src`) and for `run_app.sh` (because
`main.py` sat next to its siblings), but it isn't installable: `pip`/`pipx`
need a real Python **package** to install, and flat top-level module names
like `db_bridge` risk colliding with unrelated packages on the user's
system once installed.

Three changes made the project installable:

1. **`src/pdftui/` package.** All modules moved from `src/` into
   `src/pdftui/`, with a new `src/pdftui/__init__.py`. This is
   still the "src layout" — just with the package folder pipx/pip expect.

2. **Relative imports.** Every intra-project import changed from
   `import db_bridge` / `from manifest import ...` to
   `from . import db_bridge` / `from .manifest import ...`, so the modules
   resolve as submodules of `pdftui` instead of independent top-level
   modules.

3. **`pyproject.toml`.** Declares the package (name `pdftui`),
   its runtime dependencies (`click`, `SQLAlchemy`, `PyYAML`), and a
   console-script entry point:

   ```toml
   [project.scripts]
   pdftui = "pdftui.main:main"
   ```

   That entry point is what turns `pdftui.main.main` (the existing
   click command) into a `pdftui` shell command after install.

Nothing about the CLI's behavior, actions, or options changed — only how
the code is laid out and installed.

## Installing with pipx

From the project root (the directory containing `pyproject.toml`):

```bash
pipx install .
```

This builds an isolated virtual environment for the tool and puts a
`pdftui` command on your `PATH` (typically `~/.local/bin`).

To reinstall after making changes:

```bash
pipx install . --force
```

For active development, install in editable mode so code edits are picked
up without reinstalling:

```bash
pipx install --editable .
```

To remove it:

```bash
pipx uninstall pdftui
```

## Running the installed tool

Once installed, `pdftui` is just a regular command — run it from
wherever your manifest/PDF files live, no need to `cd` into the project
or reference `run_app.sh` / `src/` at all.

By default (`--tui` defaults to `yes`) it launches the interactive
ncurses TUI:

```bash
pdftui
```

Pass `--tui=no` to run the classic one-shot CLI instead, with `--action`
required:

```bash
pdftui --tui=no --action load_json  --main-json main.json
pdftui --tui=no --action load_yaml  --main-yaml main.yaml
pdftui --tui=no --action load_db

pdftui --tui=no --action crawl_to_json --top-dir ./my-pdfs --main-json main.json --merged-json merged.json
pdftui --tui=no --action crawl_to_yaml --top-dir ./my-pdfs --main-yaml main.yaml --saved-yaml saved.yaml
pdftui --tui=no --action crawl_to_db   --top-dir ./my-pdfs --main-json main.json
```

Run `pdftui --help` for the full option list.

## Running without installing

`run_app.sh` still works without `pipx`/`pip install` at all — it checks
whether the `pdftui` command exists on `PATH` and, if not, falls back
to running the package directly out of `src/`:

```bash
./run_app.sh --action load_json --main-json main.json
```

Likewise `run_tests.sh` / `pytest` work against `src/` via
`pythonpath = src` in `pytest.ini`, whether or not the package is
installed.
