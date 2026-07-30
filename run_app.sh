#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if command -v pdfmanifest >/dev/null 2>&1; then
    # Installed via pip/pipx -> use the console script.
    pdfmanifest "$@"
else
    # Not installed -> run straight from src/ without installing.
    # backend/src is the pdfpz git submodule (github.com/sdhube/forkpdfpz),
    # needed for pdfpz.core.class_book_manifest.PdfManifestEntry.
    PYTHONPATH="src:backend/src" /bin/python3 -m pdfmanifest.main "$@"
fi
