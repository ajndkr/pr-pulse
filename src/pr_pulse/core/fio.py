import datetime
import json
import pathlib

from rich.console import Console

from pr_pulse.config import get_config

console = Console()


def write_json_to_file(
    data: dict, prefix: str = "pr-pulse", verbose: bool = get_config().verbose
) -> None:
    """Writes JSON data to a file."""
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    filename = f"{prefix}-{today}.json"
    output_path = pathlib.Path(filename)
    output_path.write_text(json.dumps(data))
    if verbose:
        console.print(f"[green]results written to:[/] {filename}")


def write_text_to_file(
    text: str, prefix: str = "pr-pulse", verbose: bool = get_config().verbose
) -> None:
    """Writes text data to a file."""
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    filename = f"{prefix}-{today}.txt"
    output_path = pathlib.Path(filename)
    output_path.write_text(text)
    if verbose:
        console.print(f"[green]results written to:[/] {filename}")
