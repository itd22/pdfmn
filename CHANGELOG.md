# Changelog

## Unreleased (package branch)

**Added `pdfpz` as a git submodule (`backend/`), pinned to `v0.2.0`.**

- Added `github.com/sdhube/forkpdfpz` as a git submodule at `backend/`,
  so pdfmn (the TUI) can consume forkpdfpz's CLI/schema code directly
  instead of duplicating it.
- Deleted `src/pdfmanifest/manifest.py` — it was a copy of forkpdfpz's
  `PdfManifestEntry`/`is_value_containing_blacklisted_terms`. All
  consumers (`crawl.py`, `yaml_bridge.py`, `yaml_schema.py`,
  `json_bridge.py`, `books_lib.py`, `db_bridge.py`, `merge.py`, and the
  matching test files) now import `PdfManifestEntry` from
  `pdfpz.core.class_book_manifest` (the submodule) instead. No other
  file in pdfmn duplicated forkpdfpz code, so this was the only deletion.
- Checked every import across `src/` and `tests/` after the swap: no
  leftover references to the deleted module, and everything compiles.
  `entry.to_dict()`'s key set/order is unchanged, so `yaml_bridge`,
  `yaml_schema`, `json_bridge`, and `db_bridge` needed no further changes.
  (Verified the rewired imports actually resolve at runtime too, with
  both packages editable-installed — not run as part of the test suite.)
- `pyproject.toml`: documented (rather than listed as a dependency, since
  it isn't on an index) that `pdfpz` comes from the `backend` submodule —
  install with `pip install -e ./backend -e .`.
- `run_app.sh`: added `backend/src` to the no-install `PYTHONPATH`
  fallback, so the app still runs straight from source.

**Why the submodule is pinned to `v0.2.0`, not tracking a branch:**

The plan was to pin `backend` to a `v0.1.0` tag once forkpdfpz's Phase 0
(package layout) and Phase 1 (this repo dropping its duplicate schema)
had landed — a pinned tag means forkpdfpz's `dev`/`package` branches can
keep moving without silently changing what pdfmn builds against; bumping
the pin is a deliberate, reviewable step instead. In practice,
`v0.1.0` already existed on forkpdfpz pointing at an older, unrelated
commit from before the packaging work, so this milestone is tagged
`v0.2.0` instead of reusing or overwriting it. `v0.2.0` marks the first
commit where forkpdfpz has the `src/pdfpz/{core,actions}` layout, the
`pdfpz` console script, and the `class_pdf_path` importability fix — i.e.
the first point where it's actually usable as a dependency.

## Unreleased (package branch), continued

**Bumped `backend` submodule pin to `v0.3.0`; deleted `yaml_schema.py`.**

Both `pdfpz::BooksLib` and `pdfmanifest::BooksLib` turned out to hold the
same thing — `pdfpz`'s `books_manifest: Optional[BooksManifest]` wraps a
`List[PdfManifestEntry]`, and `pdfmanifest`'s `load()` returned exactly
that same list — and forkpdfpz already had its own working yaml
load/save (`BooksActions.load_books_manifest` /
`BooksManifest.save_books_manifest`) for the identical 2-document
format. So pdfmn was maintaining a second, independent yaml parser
(`yaml_schema.py`'s `entry_from_dict`/`entry_to_dict`) for data forkpdfpz
already knew how to read and write.

- forkpdfpz (`v0.3.0`): made `BooksActions.load_books_manifest` a
  `@staticmethod` — it never touched `self`, so this lets it be called
  directly as `BooksActions.load_books_manifest(path)` without
  constructing a throwaway `BooksLib` just to load a file.
- `backend` submodule pin bumped from `v0.2.0` to `v0.3.0` for that
  staticmethod change.
- `yaml_bridge.py`'s `load()`/`save()` now delegate to
  `BooksActions.load_books_manifest()` /
  `BooksManifest.save_books_manifest()` instead of
  `yaml_schema.entry_from_dict`/`entry_to_dict`. `load()` still checks
  the file exists first (matching the previous silent `[]` on a missing
  file, rather than forkpdfpz's own `print(...)` for that case).
- Deleted `src/pdfmanifest/yaml_schema.py` — with `yaml_bridge.py` no
  longer calling it, nothing else in the repo referenced it.
- Verified with a manual round-trip (save then load an entry through the
  new `yaml_bridge`, both packages editable-installed) that the format
  and field names (`Optimized` capitalization, key order, etc.) are
  unchanged — not run as part of the test suite.
- `json_bridge.py`/`db_bridge.py` are untouched: forkpdfpz has no
  equivalent for those, so there's nothing to unify there.

## Unreleased (package branch), continued again

**Renamed 4 classes and the `pdfmanifest` package itself (-> `pdftui`); bumped `backend` submodule pin to `v0.4.0`.**

Class renames (identifier-only — method, variable, and attribute names
like `books_lib`, `books_manifest`, `load_books_manifest` are unchanged):

- `pdfmanifest::Book` -> `pdfmanifest::BookOrm` (the SQLAlchemy model in
  `db_schema.py` — `Orm` makes clear it's the storage-layer row shape,
  not a domain concept).
- `pdfpz::BooksLib` -> `pdfpz::BooksCollection` (forkpdfpz, tag `v0.4.0`).
- `pdfpz::BooksManifest` -> `pdfpz::BooksShelf` (forkpdfpz, tag `v0.4.0`).
- `pdfmanifest::BooksLib` -> `pdfmanifest::BooksSpine` (this repo's
  multi-backend manifest store).

With both `BooksLib`s renamed, the naming collision from
[doc/classes.md](doc/classes.md) is gone without either side keeping a
name that no longer fit.

Package rename:

- `pdfmanifest` -> `pdftui` everywhere: `src/pdfmanifest/` ->
  `src/pdftui/`, every `from pdfmanifest.X import ...` in `src/` and
  `tests/`, `pyproject.toml` (`name`, the `[project.scripts]` entry —
  the console command itself is now `pdftui`, not just the import path),
  `run_app.sh`, `.gitignore` (including the settings filename constant,
  `.pdfmanifest_tui_settings.json` -> `.pdftui_tui_settings.json`, kept
  in sync with `tui.py`'s `SETTINGS_FILE`), `README.md`,
  `doc/DIAGRAM.md`, `doc/pipx.md`, and `.vscode/launch.json`.
- Renaming the console command (not just the import path) was a judgment
  call, not explicitly requested — leaving `pdfmanifest` as the shell
  command while everything else became `pdftui` seemed like the more
  confusing outcome, so both moved together.
- Fixed a pre-existing invalid-JSON bug in `.vscode/launch.json` (a
  missing closing quote) noticed while editing that exact line for the
  rename — unrelated to this change, so noted rather than silently
  folded in.
- `backend` submodule pin bumped `v0.3.0` -> `v0.4.0` for the
  `BooksLib`/`BooksManifest` renames above; `yaml_bridge.py` updated to
  import `BooksShelf` instead of `BooksManifest`.
- Verified end-to-end with both packages editable-installed: every
  renamed class importable under its new name from `pdftui`, the
  settings filename correct, and a save/load round-trip through the
  renamed `yaml_bridge` still works. Not run via the test suite.
- Old CHANGELOG entries above are left as written — they're a record of
  what was true when each change landed (e.g. `src/pdfmanifest/...`
  paths that no longer exist), not a description of the current tree.
