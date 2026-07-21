# pipx packaging

## What changed and why

The old `src/*.py` layout was flat modules with no package boundary. That
worked for `pytest` (via `pythonpath = src`) and for `run_app.sh` (because
`main.py` sat next to its siblings), but it isn't installable: `pip`/`pipx`
need a real Python **package** to install, and flat top-level module names
like `db_bridge` risk colliding with unrelated packages on the user's
system once installed.

Three changes made the project installable:

1. **`src/pdfmanifest/` package.** All modules moved from `src/` into
   `src/pdfmanifest/`, with a new `src/pdfmanifest/__init__.py`. This is
   still the "src layout" — just with the package folder pipx/pip expect.

2. **Relative imports.** Every intra-project import changed from
   `import db_bridge` / `from manifest import ...` to
   `from . import db_bridge` / `from .manifest import ...`, so the modules
   resolve as submodules of `pdfmanifest` instead of independent top-level
   modules.

3. **`pyproject.toml`.** Declares the package (name `pdfmanifest`),
   its runtime dependencies (`click`, `SQLAlchemy`, `PyYAML`), and a
   console-script entry point:

   ```toml
   [project.scripts]
   pdfmanifest = "pdfmanifest.main:main"
   ```

   That entry point is what turns `pdfmanifest.main.main` (the existing
   click command) into a `pdfmanifest` shell command after install.

Nothing about the CLI's behavior, actions, or options changed — only how
the code is laid out and installed.

## Installing with pipx

From the project root (the directory containing `pyproject.toml`):

```bash
pipx install .
```

This builds an isolated virtual environment for the tool and puts a
`pdfmanifest` command on your `PATH` (typically `~/.local/bin`).

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
pipx uninstall pdfmanifest
```

## Running the installed tool

Once installed, `pdfmanifest` is just a regular command — run it from
wherever your manifest/PDF files live, no need to `cd` into the project
or reference `run_app.sh` / `src/` at all.

By default (`--tui` defaults to `yes`) it launches the interactive
ncurses TUI:

```bash
pdfmanifest
```

Pass `--tui=no` to run the classic one-shot CLI instead, with `--action`
required:

```bash
pdfmanifest --tui=no --action load_json  --main-json main.json
pdfmanifest --tui=no --action load_yaml  --main-yaml main.yaml
pdfmanifest --tui=no --action load_db

pdfmanifest --tui=no --action crawl_to_json --top-dir ./my-pdfs --main-json main.json --merged-json merged.json
pdfmanifest --tui=no --action crawl_to_yaml --top-dir ./my-pdfs --main-yaml main.yaml --saved-yaml saved.yaml
pdfmanifest --tui=no --action crawl_to_db   --top-dir ./my-pdfs --main-json main.json
```

Run `pdfmanifest --help` for the full option list.

## Running without installing

`run_app.sh` still works without `pipx`/`pip install` at all — it checks
whether the `pdfmanifest` command exists on `PATH` and, if not, falls back
to running the package directly out of `src/`:

```bash
./run_app.sh --action load_json --main-json main.json
```

Likewise `run_tests.sh` / `pytest` work against `src/` via
`pythonpath = src` in `pytest.ini`, whether or not the package is
installed.
