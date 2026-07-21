from __future__ import annotations

from dataclasses import dataclass


def is_value_containing_blacklisted_terms(value: str) -> bool:
    # TODO: replace with actual blacklist check
    return False


@dataclass
class PdfManifestEntry:
    valid_pdf: bool
    file: str
    input_file: str
    title: str
    author: str
    size: int
    optimized: bool
    year: str
    isbn: str
    name: str
    # Extra field beyond the Rust struct: ISBN with hyphens/spaces stripped and
    # the check digit uppercased, for lookup/dedup use. `isbn` stays exactly
    # as it appears in the PDF text.
    isbn_normalized: str = ""
    # Extra field beyond the Rust struct: "<title>-<author>-<year>"
    book_id: str = ""
    # Extra field beyond the Rust struct: source format, currently always "pdf"
    book_type: str = "pdf"

    def scan_blacklisted_values(self):
        if is_value_containing_blacklisted_terms(self.title):
            self.title = ""
        if is_value_containing_blacklisted_terms(self.author):
            self.author = ""

    def to_dict(self) -> dict:
        return {
            "valid_pdf": self.valid_pdf,
            "input_file": self.input_file,
            "file": self.file,
            "title": self.title,
            "author": self.author,
            "size": self.size,
            "Optimized": self.optimized,
            "isbn": self.isbn,
            "name": self.name,
            "year": self.year,
            "isbn_normalized": self.isbn_normalized,
            "book_id": self.book_id,
            "book_type": self.book_type,
        }

    @classmethod
    def new_empty_manifest_entry(cls) -> "PdfManifestEntry":
        """Return a PdfManifestEntry with every field at its 'empty' value."""
        return PdfManifestEntry(
            valid_pdf=False,
            input_file="",
            file="",
            title="",
            author="",
            size=0,
            optimized=False,
            isbn="",
            name="",
            year="",
            isbn_normalized="",
            book_id="",
            book_type="pdf",
        )
