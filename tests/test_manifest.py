from pdfpz.core.class_book_manifest import PdfManifestEntry


def test_new_empty_manifest_entry_defaults():
    e = PdfManifestEntry.new_empty_manifest_entry()
    assert e.valid_pdf is False
    assert e.file == ""
    assert e.input_file == ""
    assert e.title == ""
    assert e.author == ""
    assert e.size == 0
    assert e.optimized is False
    assert e.year == ""
    assert e.isbn == ""
    assert e.name == ""
    assert e.isbn_normalized == ""
    assert e.book_id == ""
    assert e.book_type == "pdf"


def test_to_dict_key_mapping():
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.optimized = True
    d = e.to_dict()
    # optimized -> "Optimized" in the dict form
    assert d["Optimized"] is True
    assert "optimized" not in d
    assert set(d.keys()) == {
        "valid_pdf", "input_file", "file", "title", "author", "size",
        "Optimized", "isbn", "name", "year", "isbn_normalized",
        "book_id", "book_type",
    }


def test_scan_blacklisted_values_noop_when_clean():
    e = PdfManifestEntry.new_empty_manifest_entry()
    e.title = "Clean Title"
    e.author = "Clean Author"
    e.scan_blacklisted_values()
    assert e.title == "Clean Title"
    assert e.author == "Clean Author"
