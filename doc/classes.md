# Classes

All classes across both repos: `pdfmanifest` (this repo, the TUI) and
`pdfpz` (the `backend` git submodule, pinned to a tag — see
[CHANGELOG.md](../CHANGELOG.md) — pointing at
[forkpdfpz](https://github.com/sdhube/forkpdfpz)).

## All classes, alphabetically

- `pdfmanifest::Book`
- `pdfmanifest::BooksLib`
- `pdfmanifest::PdfCrawler`
- `pdfmanifest::TuiSession`
- `pdfpz::BookOperations`
- `pdfpz::BooksActions`
- `pdfpz::BooksLib`
- `pdfpz::BooksManifest`
- `pdfpz::PdfInfoExtractor`
- `pdfpz::PdfManifestEntry`
- `pdfpz::TmpPath`

Note `pdfmanifest::BooksLib` and `pdfpz::BooksLib` are two different
classes sharing one name — see the role table below and
[CHANGELOG.md](../CHANGELOG.md) for the disambiguation this repo has
already started acting on (`pdfpz::BooksLib` is paths + the current
manifest for a CLI run; `pdfmanifest::BooksLib` is the multi-backend
manifest store the TUI holds onto).

## Role

| Class | Role |
|---|---|
| `pdfmanifest::Book` | SQLAlchemy ORM model (`books` table) backing the experimental, untested sqlite storage policy. |
| `pdfmanifest::BooksLib` | Holds the in-memory entry list and dispatches load/save/crawl-merge to json, yaml, or db depending on the active policy. |
| `pdfmanifest::PdfCrawler` | Walks a directory for PDF files and builds a fresh list of manifest entries. |
| `pdfmanifest::TuiSession` | Holds everything the TUI needs across repeated actions in one run (policy, lib, parameters). |
| `pdfpz::BookOperations` | CLI flags dataclass selecting which `BooksActions` operations to run for one invocation. |
| `pdfpz::BooksActions` | CLI-side operations on a `BooksLib` — copy, sanitize, update-info, save — driven by `BookOperations` flags. |
| `pdfpz::BooksLib` | Filesystem paths (yaml/tmp/sqlite) plus the currently-loaded `BooksManifest` for one CLI run — not a list of books itself. |
| `pdfpz::BooksManifest` | `input_path` + `List[PdfManifestEntry]`, with yaml load/save and a predicate-filtered generator over the books. |
| `pdfpz::PdfInfoExtractor` | Extracts title/author/year/isbn from a PDF's legacy DocInfo dict and XMP metadata stream. |
| `pdfpz::PdfManifestEntry` | The shared per-PDF record (title/author/isbn/year/size/...) both repos build around. |
| `pdfpz::TmpPath` | Fixed set of tmp directories (`sanitized`/`metadata`/`no_info`/`renamed`) used during CLI sanitize actions. |

## Cross-package usage

Dependency direction is one-way — `pdfmanifest` depends on `pdfpz` (via
the `backend` submodule); `pdfpz` has no dependency on `pdfmanifest` and
doesn't know it exists.

| Class | Uses from the other package |
|---|---|
| `pdfmanifest::Book` | none directly — `db_bridge.py`'s module-level functions convert `Book` ↔ `pdfpz::PdfManifestEntry`, but the class itself doesn't reference it |
| `pdfmanifest::BooksLib` | `pdfpz::PdfManifestEntry` (its entry list); via `yaml_bridge`, also `pdfpz::BooksActions` and `pdfpz::BooksManifest` for the yaml policy |
| `pdfmanifest::PdfCrawler` | `pdfpz::PdfManifestEntry` (builds these while crawling) |
| `pdfmanifest::TuiSession` | none directly — goes through `pdfmanifest::BooksLib`, which uses the classes above |
| `pdfpz::BookOperations` | — |
| `pdfpz::BooksActions` | — |
| `pdfpz::BooksLib` | — |
| `pdfpz::BooksManifest` | — |
| `pdfpz::PdfInfoExtractor` | — |
| `pdfpz::PdfManifestEntry` | — |
| `pdfpz::TmpPath` | — |

`pdfpz::PdfInfoExtractor`, `pdfpz::BookOperations`, and `pdfpz::TmpPath`
aren't used by `pdfmanifest` at all yet — metadata extraction and
sanitize actions are still CLI-only features the TUI doesn't invoke.
