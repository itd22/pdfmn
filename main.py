import click

from books_lib import BooksLib

ACTIONS = ["load_json", "load_db", "crawl_to_db", "crawl_to_json"]


@click.command()
@click.option("--action", type=click.Choice(ACTIONS), required=True, help="What to do.")
@click.option("--top-dir", help="Top directory to crawl (required for crawl_to_db / crawl_to_json).")
@click.option("--main-json", default="main.json", show_default=True, help="Source manifest JSON.")
@click.option("--merged-json", default="merged.json", show_default=True, help="Output merged manifest JSON.")
def main(action, top_dir, main_json, merged_json):
    policy = "db" if action in ("load_db", "crawl_to_db") else "json"
    lib = BooksLib(policy=policy, json_path=main_json, merged_json_path=merged_json)

    if action in ("load_json", "load_db"):
        lib.load()
        lib.print_names()

    elif action in ("crawl_to_db", "crawl_to_json"):
        if not top_dir:
            raise click.UsageError("--top-dir is required for crawl_to_db / crawl_to_json")
        lib.load()
        crawled = lib.crawl_and_merge(top_dir)
        lib.save()
        click.echo(f"crawled {len(crawled)}, library now has {len(lib.entries)} entries")


if __name__ == "__main__":
    main()

