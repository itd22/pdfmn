from __future__ import annotations

from typing import List

import db_bridge
import json_bridge
from crawl import PdfCrawler
from manifest import PdfManifestEntry
from merge import merge as merge_entries


class BooksLib:
    """Holds the in-memory list of book entries and dispatches storage
    operations to json_bridge or db_bridge depending on policy.
    Only json_bridge and db_bridge are allowed to touch json/db directly.
    """

    def __init__(self, policy: str, json_path: str = "main.json", merged_json_path: str = "merged.json"):
        if policy not in ("json", "db"):
            raise ValueError(f"unknown policy: {policy}")
        self.policy = policy
        self.json_path = json_path
        self.merged_json_path = merged_json_path
        self.entries: List[PdfManifestEntry] = []

    def load(self) -> List[PdfManifestEntry]:
        if self.policy == "json":
            self.entries = json_bridge.load(self.json_path)
        else:
            if not db_bridge.is_exist():
                db_bridge.create_db()
            self.entries = db_bridge.load_all()
        return self.entries

    def print_names(self) -> None:
        for entry in self.entries:
            print(entry.name)

    def crawl_and_merge(self, top_dir: str) -> List[PdfManifestEntry]:
        crawler = PdfCrawler(top_dir)
        crawled_entries = crawler.crawl()

        if self.policy == "db":
            db_bridge.merge_to_db(crawled_entries)
            self.entries = db_bridge.load_all()
        else:
            self.entries = merge_entries(self.entries, crawled_entries)

        return crawled_entries

    def save(self) -> None:
        if self.policy == "json":
            json_bridge.save(self.merged_json_path, self.entries)
        # db policy: db_bridge.merge_to_db already persisted the changes
