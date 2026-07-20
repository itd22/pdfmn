import click

from books_lib import load_books_lib, save_books_lib
from crawl import PdfCrawler
from merge import merge


@click.command()
@click.argument("top_dir")
@click.option("--main", "main_path", default="main.json", show_default=True, help="Existing manifest JSON.")
@click.option("--merged-out", default="merged.json", show_default=True, help="Output merged manifest.")
@click.option("--crawled-out", default="crawled.json", show_default=True, help="Output raw crawl result.")
def main(top_dir, main_path, merged_out, crawled_out):
    """Crawl TOP_DIR and merge new PDFs into an existing manifest."""
    main_entries = load_books_lib(main_path)

    crawler = PdfCrawler(top_dir)
    crawled_entries = crawler.crawl()

    merged_entries = merge(main_entries, crawled_entries)

    save_books_lib(merged_out, merged_entries)
    save_books_lib(crawled_out, crawled_entries)

    click.echo(f"main: {len(main_entries)}, crawled: {len(crawled_entries)}, merged: {len(merged_entries)}")


if __name__ == "__main__":
    main()
