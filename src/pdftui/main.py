import click

from .books_lib import BooksSpine

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
@click.option(
    "--tui",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    default="yes",
    show_default=True,
    help="Launch the interactive ncurses TUI (yes) or run classic one-shot CLI mode (no).",
)
@click.option("--action", type=click.Choice(ACTIONS), required=False, help="What to do (required when --tui=no).")
@click.option("--top-dir", help="Top directory to crawl (required for crawl_to_* actions in --tui=no mode).")
@click.option("--main-json", default="main.json", show_default=True, help="Source manifest JSON.")
@click.option("--merged-json", default="merged.json", show_default=True, help="Output merged manifest JSON.")
@click.option("--main-yaml", default="main.yaml", show_default=True, help="Source manifest YAML.")
@click.option("--saved-yaml", default="saved.yaml", show_default=True, help="Output merged manifest YAML.")
@click.option("--yaml-input-path", default="", help="input_path header value written into the saved YAML.")
def main(tui, action, top_dir, main_json, merged_json, main_yaml, saved_yaml, yaml_input_path):
    if tui.lower() == "yes":
        from .tui import run_tui

        run_tui(
            top_dir=top_dir or "",
            main_json=main_json,
            merged_json=merged_json,
            main_yaml=main_yaml,
            saved_yaml=saved_yaml,
            yaml_input_path=yaml_input_path,
        )
        return

    # --tui=no: classic one-shot CLI mode, unchanged from previous versions.
    if not action:
        raise click.UsageError("--action is required when --tui=no")

    policy = POLICY_BY_ACTION[action]
    lib = BooksSpine(
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
        click.echo(f"crawled {len(crawled)}, library now has {len(lib.shelf.books)} entries")


if __name__ == "__main__":
    main()
