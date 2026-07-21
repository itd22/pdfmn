from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from . import yaml_schema
from .manifest import PdfManifestEntry


def is_exist(path: str) -> bool:
    return Path(path).exists()


def load(path: str) -> List[PdfManifestEntry]:
    """Load a 2-document books YAML file (header doc + books list doc)
    and return the books list. Missing file -> empty list."""
    p = Path(path)
    if not p.exists():
        return []

    with open(p, "r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))

    if len(docs) < 2 or not docs[1]:
        return []

    return [yaml_schema.entry_from_dict(d) for d in docs[1]]


def save(input_path: str, books_list: List[PdfManifestEntry], output_path: str = "saved.yaml") -> None:
    """Save books_list as a 2-document YAML file: header (input_path) + books list."""
    doc1 = yaml_schema.build_doc1(input_path)
    doc2 = [yaml_schema.entry_to_dict(e) for e in books_list]

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump_all([doc1, doc2], f, sort_keys=False, explicit_start=True)
