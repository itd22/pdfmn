import click

from books_lib import BooksLib

ACTIONS = ["load_json", "load_yaml", "load_db", "crawl_to_json", "crawl_to_yaml", "crawl_to_db"]

POLICY_BY_ACTION = {
    "load_json": "json",
    "crawl_to_json": "json",
    "load_yaml": "yaml",
    "crawl_to_yaml": "yaml",
    "load_db": "db",
    "crawl_to_db": "db",
}


@click.command()
@click.option("--action", type=click.Choice(ACTIONS), required=True, help="What to do.")
@click.option("--top-dir", help="Top directory to crawl (required for crawl_to_* actions).")
@click.option("--main-json", default="main.json", show_default=True, help="Source manifest JSON.")
@click.option("--merged-json", default="merged.json", show_default=True, help="Output merged manifest JSON.")
@click.option("--main-yaml", default="main.yaml", show_default=True, help="Source manifest YAML.")
@click.option("--saved-yaml", default="saved.yaml", show_default=True, help="Output merged manifest YAML.")
@click.option("--yaml-input-path", default="", help="input_path header value written into the saved YAML.")
def main(action, top_dir, main_json, merged_json, main_yaml, saved_yaml, yaml_input_path):
    policy = POLICY_BY_ACTION[action]
    lib = BooksLib(
        policy=policy,
        json_path=main_json,
        merged_json_path=merged_json,
        yaml_path=main_yaml,
        saved_yaml_path=saved_yaml,
        yaml_input_path=yaml_input_path or top_dir or "",
    )

    if action in ("load_json", "load_yaml", "load_db"):
        lib.load()
        lib.print_names()

    else:
        if not top_dir:
            raise click.UsageError("--top-dir is required for crawl_to_json / crawl_to_yaml / crawl_to_db")
        lib.load()
        crawled = lib.crawl_and_merge(top_dir)
        lib.save()
        click.echo(f"crawled {len(crawled)}, library now has {len(lib.entries)} entries")


if __name__ == "__main__":
    main()
