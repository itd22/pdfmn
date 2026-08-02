from __future__ import annotations

from typing import List

from . import db_bridge
from . import json_bridge
from . import yaml_bridge
from .crawl import PdfCrawler
from pdfpz.core.class_book_manifest import BooksShelf, PdfManifestEntry
from .merge import merge as merge_entries

POLICIES = ("json", "yaml", "db")


class BooksSpine:
    """Holds the in-memory list of book entries and dispatches storage
    operations to json_bridge, yaml_bridge, or db_bridge depending on policy.
    Only json_bridge, yaml_bridge, and db_bridge are allowed to touch
    json/yaml/db directly.

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

    def load(self) -> List[PdfManifestEntry]:
        if self.policy == "json":
            self.shelf.books = json_bridge.load(self.json_path)
        elif self.policy == "yaml":
            self.shelf.books = yaml_bridge.load(self.yaml_path)
        else:
            if not db_bridge.is_exist():
                db_bridge.create_db()
            self.shelf.books = db_bridge.load_all()
        return self.shelf.books

    def crawl_and_merge(self, top_dir: str) -> List[PdfManifestEntry]:
        crawler = PdfCrawler(top_dir)
        crawled_entries = crawler.crawl()

        if self.policy == "db":
            db_bridge.merge_to_db(crawled_entries)
            self.shelf.books = db_bridge.load_all()
        else:
            self.shelf.books = merge_entries(self.shelf.books, crawled_entries)

        return crawled_entries

    def save(self) -> None:
        if self.policy == "json":
            json_bridge.save(self.merged_json_path, self.shelf.books)
        elif self.policy == "yaml":
            yaml_bridge.save(self.yaml_input_path, self.shelf.books, self.saved_yaml_path)
        # db policy: db_bridge.merge_to_db already persisted the changes
