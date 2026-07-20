import click

import db_bridge
from books_lib import load_books_lib
from crawl import PdfCrawler


@click.command()
@click.argument("top_dir")
@click.option("--main", "main_path", default="main.json", show_default=True, help="Existing manifest JSON.")
def main(top_dir, main_path):
    """Crawl TOP_DIR and merge PDFs into the books_db database."""
    if not db_bridge.is_exist():
        main_entries = load_books_lib(main_path)
        db_bridge.create_db()
        added = db_bridge.merge_to_db(main_entries)
        click.echo(f"created db, seeded {added} entries from {main_path}")

    crawler = PdfCrawler(top_dir)
    crawled_entries = crawler.crawl()
    added = db_bridge.merge_to_db(crawled_entries)
    click.echo(f"crawled {len(crawled_entries)}, added {added} new entries")


if __name__ == "__main__":
    main()
