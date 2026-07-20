import argparse
import json
import sys

from crawl import PdfCrawler


def main():
    parser = argparse.ArgumentParser(description="Build a PDF manifest from a directory tree.")
    parser.add_argument("top_dir", help="Top directory to crawl for PDF files")
    parser.add_argument(
        "-o", "--output", default="manifest.json", help="Output JSON manifest file (default: manifest.json)"
    )
    args = parser.parse_args()

    crawler = PdfCrawler(args.top_dir)
    entries = crawler.crawl()

    manifest = [e.to_dict() for e in entries]
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(entries)} entries to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
