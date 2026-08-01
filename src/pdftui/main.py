import click

from .tui import run_tui


@click.command()
@click.option("--top-dir", help="Top directory to crawl.")
@click.option("--main-json", default="main.json", show_default=True, help="Source manifest JSON.")
@click.option("--merged-json", default="merged.json", show_default=True, help="Output merged manifest JSON.")
@click.option("--main-yaml", default="main.yaml", show_default=True, help="Source manifest YAML.")
@click.option("--saved-yaml", default="saved.yaml", show_default=True, help="Output merged manifest YAML.")
@click.option("--yaml-input-path", default="", help="input_path header value written into the saved YAML.")
def main(top_dir, main_json, merged_json, main_yaml, saved_yaml, yaml_input_path):
    run_tui(
        top_dir=top_dir or "",
        main_json=main_json,
        merged_json=merged_json,
        main_yaml=main_yaml,
        saved_yaml=saved_yaml,
        yaml_input_path=yaml_input_path,
    )


if __name__ == "__main__":
    main()
