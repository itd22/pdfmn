# pdfpz / pdftui architecture review (package74)

## The "one source → memory → screen" pipeline mostly holds

For `PdfManifestEntry`/`BooksShelf`, this is real and clean:

- **Memory**: `BooksSpine.shelf` (a `pdfpz.BooksShelf`) is the single in-memory
  collection. `TuiSession.get_lib()` builds it once and reuses it across
  actions — it's never rebuilt as a side effect.
- **Storage → memory**: `json_bridge`, `yaml_bridge`, `db_bridge` are three
  interchangeable ways to fill `shelf.books` from disk/DB. Each converts its
  native format to `PdfManifestEntry` via its own adapter (`entry_from_dict`/
  `to_dict` for json; `PdfManifestEntry.from_dict`/`to_dict` via
  `BooksCollection` for yaml; `_book_to_entry`/`_entry_to_book` for db) — none
  of them leak their format's shape past that boundary.
- **Memory → screen**: `PdftuiApp._refresh_table()` reads `controller.entries()`
  (→ `session.lib.shelf.books`) and nothing else. The table never reads a file
  or the DB directly.

This is already a **Strategy pattern**, just an informal one: `BooksSpine.load()`/
`.save()` branch on `self.policy` with `if/elif/else`, picking one of three
same-shaped `load(path) -> List[PdfManifestEntry]` / `save(...)` functions.
Worth formalizing — a `StorageBridge` `Protocol` the three bridge modules
already structurally satisfy, then:
```python
BRIDGES = {"json": json_bridge, "yaml": yaml_bridge, "db": db_bridge}
...
def load(self):
    self.shelf.books = BRIDGES[self.policy].load(self._path_for(self.policy))
```
turns the branching into a dict lookup and makes a 4th backend a one-line
addition instead of a new `elif`.

## Where it breaks: Props aren't a representation of "the same data" yet

`PdfProps` (orig/sanitized/metadata/renamed/sphostscript) is real per-book
data, same as title/author — but it doesn't flow through the pipeline above
at all:

- `PdfManifestEntry` has no props fields.
- `json_bridge`/`yaml_bridge` have no concept of props — only `db_bridge`
  (via `BookOrm`/`BookPropsOrm`) does.
- `BookPropsActions` talks to the sqlite tables directly, correlated to a
  book only by a separately-looked-up `id`/`name` — it doesn't go through
  `BooksShelf` or any bridge.
- The result is visible in the UI's own logic: "Update Props" explicitly
  checks `db_bridge.is_exist()` and refuses ("must be saved as DB first")
  under the json/yaml policies. Props are a **db-only aggregate**, not a
  representation of the same entries json/yaml also hold.

Two honest ways to resolve this, not a "just fix it":
1. **Fold props into `PdfManifestEntry`** (add the 5 fields) and extend
   `json_bridge`/`yaml_bridge` to (de)serialize them too. Now props really
   are "the same data, 3 representations," and `BookPropsActions` collapses
   into ordinary entry fields updated in place.
2. **Keep Props a separate, explicitly db-only aggregate** with its own
   repository (what exists today) — but document it as an intentional
   design decision (a "Props" concept nothing else needs y/json for) rather
   than leaving the asymmetry implicit and only discoverable by reading
   `update_props_from_filesystem`'s guard clause.

Given the button already gates on `db_bridge.is_exist()`, option 2 seems to
be the direction already being taken — worth making that explicit in
`BooksCollection`/`BooksShelf`'s docstrings so it doesn't read as an
oversight later.

## A second observation: two Facades over the same lower layer

`BooksActions` (`cli.py`'s path) and `BooksSpine`+bridges (`pdftui`'s path)
both end up constructing/using a `BooksCollection` to load or save yaml —
`BooksActions.load_books_manifest` builds one via
`self.books_collection.load_books_collection()`, `yaml_bridge.load` builds
one via `BooksCollection.from_legacy_path(path)` then the same
`.load_books_collection()`. The actual I/O only happens once (inside
`BooksCollection`/`AssetsLegacy`, correctly not duplicated) — but the
"construct a `BooksCollection` for this path and load/extract books" sequence
is written twice, once per Facade. Since `cli.py` and `pdftui` are genuinely
different front-ends (batch vs. interactive), having two Facades is
reasonable — but `yaml_bridge.load`/`save` could *be* what
`BooksActions.load_books_manifest`/`save_books_collection_yaml` call, rather
than each re-deriving the construction step independently.

## Summary of applicable patterns

| Pattern | Where it already fits | Suggested next step |
|---|---|---|
| Strategy | `BooksSpine` picking json/yaml/db per `self.policy` | Formalize as a `StorageBridge` protocol + dict dispatch |
| Adapter | Each bridge's dict/ORM ↔ `PdfManifestEntry` conversion | Already clean, no change needed |
| Repository | `BooksSpine` (in-memory collection + swappable persistence) | Decide if Props is part of the same aggregate or a separate one (see above) |
| Facade | `BooksActions` (cli.py) and `BooksSpine` (pdftui) | Have `BooksActions` call the bridges instead of re-deriving `BooksCollection` construction |
