import yaml

from pdfmanifest.manifest import PdfManifestEntry
from pdfmanifest.yaml_bridge import is_exist, load, save


def test_load_missing_file_returns_empty_list(tmp_path):
    assert load(str(tmp_path / "nope.yaml")) == []


def test_is_exist(tmp_path):
    p = tmp_path / "main.yaml"
    assert is_exist(str(p)) is False
    p.write_text("---\ninput_path: /x\n---\n[]\n")
    assert is_exist(str(p)) is True


def test_load_two_document_yaml(tmp_path):
    p = tmp_path / "main.yaml"
    p.write_text(
        "---\n"
        "input_path: /home/sd/gitlab_books\n"
        "---\n"
        "- valid_pdf: false\n"
        "  input_file: ./book.pdf\n"
        "  file: book.pdf\n"
        "  title: ''\n"
        "  author: ''\n"
        "  size: 0\n"
        "  Optimized: false\n"
        "  isbn: ''\n"
        "  name: book\n"
        "  year: ''\n"
        "  isbn_normalized: ''\n"
        "  book_id: ''\n"
        "  book_type: pdf\n"
    )
    entries = load(str(p))
    assert len(entries) == 1
    assert entries[0].name == "book"
    assert entries[0].input_file == "./book.pdf"


def test_save_writes_two_documents_and_round_trips(tmp_path):
    out = tmp_path / "saved.yaml"
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.name = "a"
    e.optimized = True

    save("/some/input/path", [e], str(out))

    with open(out) as f:
        docs = list(yaml.safe_load_all(f))

    assert len(docs) == 2
    assert docs[0] == {"input_path": "/some/input/path"}
    assert docs[1][0]["name"] == "a"
    assert docs[1][0]["Optimized"] is True

    reloaded = load(str(out))
    assert len(reloaded) == 1
    assert reloaded[0].name == "a"
    assert reloaded[0].optimized is True
