# PDF Manifest — Architecture

## Responsibilities

| File            | Responsibility                                                             |
|------------------|-----------------------------------------------------------------------------|
| `manifest.py`    | `PdfManifestEntry` dataclass — the record shape. No I/O.                   |
| `crawl.py`       | `PdfCrawler` — walks a directory tree, returns `List[PdfManifestEntry]`.   |
| `json_bridge.py` | Only module that reads/writes the JSON manifest files.                    |
| `db_bridge.py`   | Only module that talks to `books_db.sqlite` (via `db_schema.py`).         |
| `db_schema.py`   | SQLAlchemy `Book` table definition.                                       |
| `merge.py`       | Pure in-memory merge: add-only-new-by-`name`. Used for the json policy.   |
| `books_lib.py`   | `BooksLib` — holds the entry list, picks json_bridge vs db_bridge by policy. |
| `main.py`        | CLI (click) — reads `--action`, builds `BooksLib` with the right policy, calls `load` / `crawl_and_merge` / `save` / `print_names`. |

Rule: **only `json_bridge.py` and `db_bridge.py` touch storage.**
`books_lib.py` and `main.py` never open a file or a DB connection directly.

## Class diagram

```mermaid
classDiagram
    class PdfManifestEntry {
        +valid_pdf bool
        +file str
        +input_file str
        +title str
        +author str
        +size int
        +optimized bool
        +year str
        +isbn str
        +name str
        +isbn_normalized str
        +book_id str
        +book_type str
        +to_dict() dict
        +new_empty_manifest_entry() PdfManifestEntry
    }

    class PdfCrawler {
        +top_dir Path
        +crawl() List~PdfManifestEntry~
    }

    class BooksLib {
        +policy str
        +entries List~PdfManifestEntry~
        +load() List~PdfManifestEntry~
        +crawl_and_merge(top_dir) List~PdfManifestEntry~
        +save() void
        +print_names() void
    }

    class json_bridge {
        <<module>>
        +is_exist(path) bool
        +load(path) List~PdfManifestEntry~
        +save(path, entries) void
    }

    class db_bridge {
        <<module>>
        +is_exist() bool
        +create_db() void
        +load_all() List~PdfManifestEntry~
        +save(entries) void
        +merge_to_db(entries) int
    }

    class merge {
        <<module>>
        +merge(main_entries, additional_entries) List~PdfManifestEntry~
    }

    class Book {
        <<sqlalchemy model>>
        +id int
        +...same fields as PdfManifestEntry
    }

    BooksLib --> json_bridge : policy == "json"
    BooksLib --> db_bridge : policy == "db"
    BooksLib --> merge : policy == "json" (in-memory merge)
    BooksLib --> PdfCrawler : crawl_and_merge()
    PdfCrawler --> PdfManifestEntry : creates
    json_bridge --> PdfManifestEntry : (de)serializes
    db_bridge --> Book : reads/writes rows
    db_bridge --> PdfManifestEntry : converts Book <-> entry
    db_bridge ..> db_schema : uses Base/Book
```

## Flow — `main.py --action <...>`

```mermaid
flowchart TD
    A[main.py: parse --action] --> B{action}

    B -->|load_json| C1[policy = json]
    B -->|load_db| C2[policy = db]
    B -->|crawl_to_json| C1
    B -->|crawl_to_db| C2

    C1 --> D[BooksLib policy=json]
    C2 --> E[BooksLib policy=db]

    D --> F[lib.load]
    E --> F

    F -->|json| F1[json_bridge.load main.json]
    F -->|db, not is_exist| F2[db_bridge.create_db + load_all -> empty]
    F -->|db, is_exist| F3[db_bridge.load_all]

    B -->|load_json / load_db| G[lib.print_names]

    B -->|crawl_to_json / crawl_to_db| H[lib.crawl_and_merge top_dir]
    H --> H1[PdfCrawler.crawl -> crawled_entries]
    H1 -->|json policy| H2[merge.merge main+crawled, in memory]
    H1 -->|db policy| H3[db_bridge.merge_to_db crawled_entries]

    H2 --> I[lib.save]
    H3 --> I
    I -->|json policy| I1[json_bridge.save merged.json]
    I -->|db policy| I2[no-op, already persisted by merge_to_db]
```

## Actions summary

- **load_json** — read `main.json`, print names.
- **load_db** — open/create `books_db.sqlite`, print names.
- **crawl_to_json** — load `main.json`, crawl `--top-dir`, merge in memory (unique by `name`), write `merged.json`.
- **crawl_to_db** — if `books_db.sqlite` doesn't exist: create it and seed from `main.json`; then crawl `--top-dir` and merge new entries (unique by `name`) directly into the DB.
