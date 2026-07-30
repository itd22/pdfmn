from __future__ import annotations

from typing import Any, Dict

from pdfpz.core.class_book_manifest import PdfManifestEntry

# Document 1: header metadata
INPUT_PATH_KEY = "input_path"

# Document 2: list of book entries.
# Key order/names mirror PdfManifestEntry.to_dict() exactly (Optimized is
# capitalized there too), so the schema and to_dict() stay in sync.
ENTRY_FIELD_MAP = {
    "valid_pdf": "valid_pdf",
    "input_file": "input_file",
    "file": "file",
    "title": "title",
    "author": "author",
    "size": "size",
    "Optimized": "optimized",
    "isbn": "isbn",
    "name": "name",
    "year": "year",
    "isbn_normalized": "isbn_normalized",
    "book_id": "book_id",
    "book_type": "book_type",
}


def build_doc1(input_path: str) -> Dict[str, Any]:
    return {INPUT_PATH_KEY: input_path}


def get_input_path(doc1: Dict[str, Any]) -> str:
    return doc1.get(INPUT_PATH_KEY, "") if doc1 else ""


def entry_to_dict(entry: PdfManifestEntry) -> Dict[str, Any]:
    return entry.to_dict()


def entry_from_dict(d: Dict[str, Any]) -> PdfManifestEntry:
    entry = PdfManifestEntry.new_empty_manifest_entry()
    for key, field in ENTRY_FIELD_MAP.items():
        if key in d:
            setattr(entry, field, d[key])
    return entry
