import json
from pathlib import Path

import typer
from rich.console import Console

from pr_pulse import utils
from pr_pulse.constants import REPORT_PROMPT

app = typer.Typer()
console = Console()


@app.command()
def ai_report(
    summary_json_file: Path = typer.Argument(
        ...,
        help="Path to summary JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    api_key: str = typer.Option(
        None,
        help="GEMINI API key. if not provided, will try to use GENAI_API_KEY environment variable",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
):
    """Generates a report of pull request activity from a JSON file using Gemini AI."""
    try:
        client = utils.setup_gemini_client(api_key, verbose)
        model = "gemini-2.0-flash"

        if verbose:
            console.print("[bold blue]reading[/] input file...")

        try:
            with open(summary_json_file, "r") as f:
                input_data = f.read()
        except Exception as e:
            console.print(f"[bold red]error:[/] failed to read input file: {str(e)}")
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]generating[/] summary...")

        response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=REPORT_PROMPT.format(input_data=input_data),
        ):
            if stream:
                console.print(chunk.text, end="")
            response += chunk.text

        if not stream:
            console.print(response)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
