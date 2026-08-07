# pdfpz / pdftui architecture review (package74)

## Pipeline status: Works for books, breaks for props

**Storage → Memory → Screen** flows cleanly for `PdfManifestEntry`/`BooksShelf`:
- Single source of truth: `BooksShelf.shelf` in memory
- Three interchangeable backends: json/yaml/db via bridge adapters
- UI reads from memory only, never directly from disk/DB

**Props are the exception:**
- `PdfProps` (orig/sanitized/metadata/renamed/ghostscript) only exist in DB
- Not part of `PdfManifestEntry`, not serialized by json/yaml bridges
- `BookPropsActions` talks to sqlite directly, bypassing `BooksShelf`
- UI gates "Update Props" behind `db_bridge.is_exist()` — props are db-only

**Resolution needed:**
1. Fold props into `PdfManifestEntry` and extend json/yaml bridges, OR
2. Document props as intentionally db-only (seems to be the chosen direction)

## Two facades doing duplicate work

`BooksActions` (CLI) and `BooksSpine` (UI) both construct `BooksCollection` for yaml independently. Have `BooksActions` call the bridges instead.

## Suggested refactors

| Pattern | Current state | Next step |
|---|---|---|
| Strategy | `BooksSpine` branches on `self.policy` | Formalize as `StorageBridge` protocol + dict dispatch |
| Adapter | Each bridge's dict/ORM ↔ `PdfManifestEntry` | Already clean ✓ |
| Repository | `BooksSpine` + swappable persistence | Clarify: props in aggregate or separate? |
| Facade | `BooksActions` + `BooksSpine` | Have `BooksActions` call bridges, not re-derive construction |
