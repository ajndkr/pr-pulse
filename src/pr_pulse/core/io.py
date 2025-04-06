import datetime
import json
from pathlib import Path
from typing import Any

from rich.console import Console

from pr_pulse.config import get_config

console = Console()


class FileIOError(Exception):
    """Exception raised for file I/O errors"""

    pass


def get_output_filename(prefix: str, extension: str) -> str:
    """Generate a filename with timestamp"""
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    return f"{prefix}-{today}.{extension}"


def write_to_file(content: str, filepath: str) -> None:
    """Write content to a file"""
    try:
        Path(filepath).write_text(content)
    except Exception as e:
        raise FileIOError(f"Failed to write to file {filepath}: {str(e)}")


def write_json_to_file(
    data: dict[str, Any],
    prefix: str = get_config().file_prefix,
    verbose: bool = get_config().verbose,
) -> str:
    """Write JSON data to a file"""
    try:
        output_path = get_output_filename(prefix, "json")
        write_to_file(json.dumps(data), output_path)

        if verbose:
            console.print(f"[green]results written to:[/] {output_path}")

        return output_path
    except Exception as e:
        error_msg = f"Unexpected error writing JSON file: {str(e)}"
        console.print(f"[bold red]error:[/] {error_msg}")
        raise FileIOError(error_msg)


def write_text_to_file(
    text: str,
    prefix: str = get_config().file_prefix,
    verbose: bool = get_config().verbose,
) -> str:
    """Write text data to a file"""
    try:
        output_path = get_output_filename(prefix, "txt")
        write_to_file(text, output_path)

        if verbose:
            console.print(f"[green]results written to:[/] {output_path}")

        return output_path
    except Exception as e:
        error_msg = f"Unexpected error writing text file: {str(e)}"
        console.print(f"[bold red]error:[/] {error_msg}")
        raise FileIOError(error_msg)
