# Classes

All classes across both repos: `pdftui` (this repo, the TUI) and
`pdfpz` (the `backend` git submodule, pointing at
[forkpdfpz](https://github.com/sdhube/forkpdfpz)).

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

## Role

| Class | Role |
|---|---|
| `pdftui::BookOrm` | SQLAlchemy ORM model (`books` table) backing the experimental, untested sqlite storage policy. |
| `pdftui::BooksSpine` | Holds the in-memory entry list — a `pdfpz::BooksShelf` (`self.shelf`) — and dispatches load/save/crawl-merge to json, yaml, or db depending on the active policy. |
| `pdftui::PdfCrawler` | Walks a directory for PDF files and builds a fresh list of manifest entries. |
| `pdftui::TuiSession` | Holds everything the TUI needs across repeated actions in one run (policy, lib, parameters). |
| `pdfpz::BookOperations` | CLI flags dataclass selecting which `BooksActions` operations to run for one invocation. |
| `pdfpz::BooksActions` | CLI-side operations on a `BooksCollection` — copy, sanitize, update-info, save — driven by `BookOperations` flags. |
| `pdfpz::BooksCollection` | Filesystem paths (yaml/tmp/sqlite) + `input_path`, plus the currently-loaded `BooksShelf` — and `save_books_manifest()`, so it's also where persistence for one CLI run actually happens. |
| `pdfpz::BooksShelf` | Just the books and how to look at them: `books: List[PdfManifestEntry]` + a predicate-filtered generator (`books_generator`). No I/O of its own. |
| `pdfpz::PdfInfoExtractor` | Extracts title/author/year/isbn from a PDF's legacy DocInfo dict and XMP metadata stream, writing onto a bound `PdfManifestEntry`. |
| `pdfpz::PdfManifestEntry` | The shared per-PDF record (title/author/isbn/year/size/...) both repos build around. |
| `pdfpz::TmpPath` | Fixed set of tmp directories (`sanitized`/`metadata`/`no_info`/`renamed`), each exposed via its own `path_*` property, used during CLI sanitize actions. |

## Cross-package usage (pdftui <-> pdfpz)

Dependency direction is one-way — `pdftui` depends on `pdfpz` (via the
`backend` submodule); `pdfpz` has no dependency on `pdftui` and doesn't
know it exists.

| Class | Uses from the other package |
|---|---|
| `pdftui::BookOrm` | none directly — `db_bridge.py`'s module-level functions convert `BookOrm` ↔ `pdfpz::PdfManifestEntry`, but the class itself doesn't reference it |
| `pdftui::BooksSpine` | `pdfpz::BooksShelf` (`self.shelf` — its own entry-list wrapper, used across every policy, not just yaml); `pdfpz::PdfManifestEntry` (the entries inside it); via `yaml_bridge`, also `pdfpz::BooksActions` and `pdfpz::BooksCollection` for the yaml policy specifically — `yaml_bridge.load()` calls `BooksActions.load_books_manifest()`, `yaml_bridge.save()` builds a `BooksCollection` and calls its `save_books_manifest()` |
| `pdftui::PdfCrawler` | `pdfpz::PdfManifestEntry` (via `new_empty_manifest_entry()`, while crawling) |
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
| `pdfpz::BooksActions` | `BooksCollection` (constructor param, `self.books_collection`, including `save_books_collection_yaml`'s `self.books_collection.save_books_manifest()`); `BooksShelf` (`load_books_manifest`'s return type and construction, `self.books_collection.books_manifest`); `PdfManifestEntry` (iterates/filters entries throughout); `TmpPath` (sanitize-path lookup in `sanitize_books_info`) |
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
