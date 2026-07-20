import argparse
import sys

from books_lib import load_books_lib, save_books_lib
from crawl import PdfCrawler
from merge import merge


def main():
    parser = argparse.ArgumentParser(description="Crawl a directory and merge new PDFs into an existing manifest.")
    parser.add_argument("top_dir", help="Top directory to crawl for PDF files")
    parser.add_argument("--main", default="main.json", help="Existing manifest JSON (default: main.json)")
    parser.add_argument("--merged-out", default="merged.json", help="Output merged manifest (default: merged.json)")
    parser.add_argument("--crawled-out", default="crawled.json", help="Output raw crawl result (default: crawled.json)")
    args = parser.parse_args()

    main_entries = load_books_lib(args.main)

    crawler = PdfCrawler(args.top_dir)
    crawled_entries = crawler.crawl()

    merged_entries = merge(main_entries, crawled_entries)

    save_books_lib(args.merged_out, merged_entries)
    save_books_lib(args.crawled_out, crawled_entries)

    print(f"main: {len(main_entries)}, crawled: {len(crawled_entries)}, merged: {len(merged_entries)}")


if __name__ == "__main__":
    sys.exit(main())
