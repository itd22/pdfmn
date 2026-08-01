# Classes

All classes across both repos: `pdftui` (this repo, the TUI — package
renamed from `pdfmanifest`, see [CHANGELOG.md](../CHANGELOG.md)) and
`pdfpz` (the `backend` git submodule, currently pinned to `v0.5.0` —
pointing at [forkpdfpz](https://github.com/sdhube/forkpdfpz)).

## All classes, alphabetically

- `pdftui::BookOrm`
- `pdftui::BooksSpine`
- `pdftui::PdfCrawler`
- `pdftui::TuiSession`
- `pdfpz::BookOperations`
- `pdfpz::BooksActions`
- `pdfpz::BooksCollection`
- `pdfpz::BooksShelf`
- `pdfpz::PdfInfoExtractor`
- `pdfpz::PdfManifestEntry`
- `pdfpz::TmpPath`

Earlier, `pdftui::BooksSpine` and `pdfpz::BooksCollection` were both
named `BooksLib`, and `pdfpz::BooksShelf` was named `BooksManifest` —
see [CHANGELOG.md](../CHANGELOG.md) for that rename and why (both
`BooksLib`s held the same underlying `List[PdfManifestEntry]`, wrapped
differently). `pdftui::BookOrm` was `Book` before this rename, renamed
to make clear it's the storage-layer row shape, not a domain concept.

After the rename, `pdfpz::BooksShelf` and `pdfpz::BooksCollection` also
had their responsibilities re-split: `BooksShelf` used to carry
`input_path` and `save_books_manifest(yaml_path)` itself; both moved to
`BooksCollection`, which now owns persistence (`save_books_manifest()`,
no arguments — writes `self.books_manifest` to `self.yaml_path`) while
`BooksShelf` is left as just the books list plus filtering. That move
also fixed a real bug: `BooksActions.save_books_lib_yaml` used to always
write to a hardcoded `./files_info.yaml` regardless of which file was
loaded; it now correctly writes back to `self.books_lib.yaml_path`.

## Role

| Class | Role |
|---|---|
| `pdftui::BookOrm` | SQLAlchemy ORM model (`books` table) backing the experimental, untested sqlite storage policy. |
| `pdftui::BooksSpine` | Holds the in-memory entry list and dispatches load/save/crawl-merge to json, yaml, or db depending on the active policy. |
| `pdftui::PdfCrawler` | Walks a directory for PDF files and builds a fresh list of manifest entries. |
| `pdftui::TuiSession` | Holds everything the TUI needs across repeated actions in one run (policy, lib, parameters). |
| `pdfpz::BookOperations` | CLI flags dataclass selecting which `BooksActions` operations to run for one invocation. |
| `pdfpz::BooksActions` | CLI-side operations on a `BooksCollection` — copy, sanitize, update-info, save — driven by `BookOperations` flags. |
| `pdfpz::BooksCollection` | Filesystem paths (yaml/tmp/sqlite) + `input_path`, plus the currently-loaded `BooksShelf` — and now `save_books_manifest()`, so it's also where persistence for one CLI run actually happens. |
| `pdfpz::BooksShelf` | Just the books and how to look at them: `books: List[PdfManifestEntry]` + a predicate-filtered generator (`books_generator`). No I/O of its own anymore. |
| `pdfpz::PdfInfoExtractor` | Extracts title/author/year/isbn from a PDF's legacy DocInfo dict and XMP metadata stream, writing onto a bound `PdfManifestEntry`. |
| `pdfpz::PdfManifestEntry` | The shared per-PDF record (title/author/isbn/year/size/...) both repos build around. |
| `pdfpz::TmpPath` | Fixed set of tmp directories (`sanitized`/`metadata`/`no_info`/`renamed`) used during CLI sanitize actions. |

## Cross-package usage (pdftui <-> pdfpz)

Dependency direction is one-way — `pdftui` depends on `pdfpz` (via the
`backend` submodule); `pdfpz` has no dependency on `pdftui` and doesn't
know it exists.

| Class | Uses from the other package |
|---|---|
| `pdftui::BookOrm` | none directly — `db_bridge.py`'s module-level functions convert `BookOrm` ↔ `pdfpz::PdfManifestEntry`, but the class itself doesn't reference it |
| `pdftui::BooksSpine` | `pdfpz::PdfManifestEntry` (its entry list); via `yaml_bridge`, also `pdfpz::BooksActions`, `pdfpz::BooksCollection`, and `pdfpz::BooksShelf` for the yaml policy — `yaml_bridge.save()` builds a `BooksCollection` (holding a `BooksShelf`) and calls its `save_books_manifest()` directly |
| `pdftui::PdfCrawler` | `pdfpz::PdfManifestEntry` (builds these while crawling) |
| `pdftui::TuiSession` | none directly — goes through `pdftui::BooksSpine`, which uses the classes above |
| `pdfpz::BookOperations` | — |
| `pdfpz::BooksActions` | — |
| `pdfpz::BooksCollection` | — |
| `pdfpz::BooksShelf` | — |
| `pdfpz::PdfInfoExtractor` | — |
| `pdfpz::PdfManifestEntry` | — |
| `pdfpz::TmpPath` | — |

`pdfpz::PdfInfoExtractor`, `pdfpz::BookOperations`, and `pdfpz::TmpPath`
aren't used by `pdftui` at all yet — metadata extraction and sanitize
actions are still CLI-only features the TUI doesn't invoke.

## `pdfpz`-internal class dependencies

Which `pdfpz` classes reference which other `pdfpz` classes, based on
constructor params, field types, and method bodies in
`backend/src/pdfpz/`:

| Class | Depends on (other `pdfpz` classes) |
|---|---|
| `pdfpz::BookOperations` | — |
| `pdfpz::BooksActions` | `BooksCollection` (constructor param, `self.books_lib`, including `save_books_lib_yaml`'s `self.books_lib.save_books_manifest()`); `BooksShelf` (`load_books_manifest`'s return type and construction, `self.books_lib.books_manifest`); `PdfManifestEntry` (iterates/filters entries throughout); `TmpPath` (sanitize-path lookup in `sanitize_books_info`) |
| `pdfpz::BooksCollection` | `BooksShelf` (its `books_manifest: Optional[BooksShelf]` field, and `self.books_manifest.books` inside its own `save_books_manifest()`) |
| `pdfpz::BooksShelf` | `PdfManifestEntry` (its `books: List[PdfManifestEntry]` field) |
| `pdfpz::PdfInfoExtractor` | `PdfManifestEntry` (constructor param `entry`, and the `blank()`/`for_entry()` creational methods) |
| `pdfpz::PdfManifestEntry` | — |
| `pdfpz::TmpPath` | — |

`PdfManifestEntry` and `TmpPath` are the leaves — everything else in
`pdfpz` is built on top of one or both of them, directly or (in
`BooksActions`' case) transitively through `BooksCollection`/`BooksShelf`.
`BookOperations` stands alone — it's just a flags dataclass consumed by
`cli.py`, not referenced by any other `pdfpz` class.
