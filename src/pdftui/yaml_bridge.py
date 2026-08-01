from __future__ import annotations

from pathlib import Path
from typing import List

from pdfpz.actions.class_books_actions import BooksActions
from pdfpz.core.class_book_manifest import BooksCollection, BooksShelf, PdfManifestEntry


def is_exist(path: str) -> bool:
    return Path(path).exists()


def load(path: str) -> List[PdfManifestEntry]:
    """Load a 2-document books YAML file (header doc + books list doc)
    and return the books list. Missing file -> empty list.

    Delegates the actual parsing to pdfpz's BooksActions.load_books_manifest,
    which reads the same 2-document format for the same PdfManifestEntry
    list -- so this module no longer keeps a second, independent yaml
    parser (the old yaml_schema.py) in sync with it.
    """
    if not is_exist(path):
        return []

    manifest = BooksActions.load_books_manifest(path)
    return manifest.books if manifest else []


def save(input_path: str, books_list: List[PdfManifestEntry], output_path: str = "saved.yaml") -> None:
    """Save books_list as a 2-document YAML file: header (input_path) + books list.

    Delegates to pdfpz's BooksCollection.save_books_manifest for the same
    reason. BooksCollection.save_books_manifest() takes no arguments and
    always writes to its own yaml_path, so this builds a one-off
    BooksCollection around output_path/input_path/books_list rather than
    keeping one around between calls -- nothing here persists a
    BooksCollection across saves today.
    """
    collection = BooksCollection.from_yaml_path(output_path)
    collection.input_path = input_path
    collection.books_manifest = BooksShelf(books=list(books_list))
    collection.save_books_manifest()
