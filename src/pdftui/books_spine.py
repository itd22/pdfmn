from __future__ import annotations

from typing import List

from pdfpz.bridges import db_bridge, json_bridge
from pdfpz.core.class_book_manifest import BooksShelf, PdfManifestEntry
from pdfpz.core.class_books_collection import BooksCollection

POLICIES = ("json", "yaml", "db")


class BooksSpine:
    """Holds the in-memory list of book entries and dispatches storage
    operations to json_bridge, BooksCollection (yaml), or db_bridge
    depending on policy. Only json_bridge, BooksCollection/AssetsLegacy,
    and db_bridge are allowed to touch json/yaml/db directly.

    Crawling and crawl+merge logic now live on BooksCollection
    (pdfpz.core.class_books_collection) -- they operate purely on the
    in-memory books list, independent of the persistence backend, so they
    moved to the same package as the rest of the domain model instead of
    living here. json/db policies don't have an Asset-backed collection
    yet, so BooksSpine still talks to json_bridge/db_bridge directly for
    those; only the yaml policy is routed through BooksCollection so far.

    The entry list itself is a pdfpz.core.class_book_manifest.BooksShelf
    (self.shelf), reused directly rather than reimplemented -- BooksSpine
    used to keep its own bare list for exactly the "list of
    PdfManifestEntry + a way to look at it" role pdfpz::BooksShelf
    already covers. No backward-compatible `entries` alias is kept --
    callers read/write self.shelf.books directly.
    """

    def __init__(
        self,
        policy: str,
        json_path: str = "main.json",
        merged_json_path: str = "merged.json",
        yaml_path: str = "main.yaml",
        saved_yaml_path: str = "saved.yaml",
        yaml_input_path: str = "",
    ):
        if policy not in POLICIES:
            raise ValueError(f"unknown policy: {policy}")
        self.policy = policy
        self.json_path = json_path
        self.merged_json_path = merged_json_path
        self.yaml_path = yaml_path
        self.saved_yaml_path = saved_yaml_path
        self.yaml_input_path = yaml_input_path
        self.shelf: BooksShelf = BooksShelf()

    def _yaml_collection(self, path: str) -> BooksCollection:
        """Build a BooksCollection for the yaml policy, wired to this
        spine's current shelf so load/save/crawl_and_merge share state
        with self.shelf."""
        collection = BooksCollection.from_legacy_path(path)
        collection.books_manifest = self.shelf
        return collection

    def load(self) -> List[PdfManifestEntry]:
        if self.policy == "json":
            self.shelf.books = json_bridge.load(self.json_path)
        elif self.policy == "yaml":
            collection = self._yaml_collection(self.yaml_path)
            collection.load_books_collection()
            self.shelf = collection.books_manifest
        else:
            if not db_bridge.is_exist():
                db_bridge.create_db()
            self.shelf.books = db_bridge.load_all()
        return self.shelf.books

    def crawl_and_merge(self, top_dir: str) -> List[PdfManifestEntry]:
        if self.policy == "db":
            from pdfpz.core.crawl import PdfCrawler

            crawler = PdfCrawler(top_dir)
            crawled_entries = crawler.crawl()
            db_bridge.merge_to_db(crawled_entries)
            self.shelf.books = db_bridge.load_all()
            return crawled_entries

        # json and yaml policies: crawl+merge is backend-independent, so
        # delegate to BooksCollection (it only touches books_manifest,
        # never self.assets, for this call).
        collection = BooksCollection(sqlite_path="", books_manifest=self.shelf, tmp_path="", assets=None)
        crawled_entries = collection.crawl_and_merge(top_dir)
        self.shelf = collection.books_manifest
        return crawled_entries

    def save(self) -> None:
        if self.policy == "json":
            json_bridge.save(self.merged_json_path, self.shelf.books)
        elif self.policy == "yaml":
            collection = self._yaml_collection(self.saved_yaml_path)
            collection.assets.input_path = self.yaml_input_path
            collection.books_manifest = self.shelf
            collection.save_books_collection()
        # db policy: db_bridge.merge_to_db already persisted the changes
