import json
from pathlib import Path

import typer
from google.genai import types
from rich.console import Console

from pr_pulse.constants import REPORT_PROMPT
from pr_pulse.core import clients, fio

app = typer.Typer(
    help="Analyze PR data and generate Pulse insights",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def summary(
    details_json_file: Path = typer.Argument(
        ...,
        help="Path to details JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    api_key: str = typer.Option(
        None,
        help="GEMINI API key. if not provided, will try to use default config",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
    write: bool = typer.Option(
        False, "--write", "-w", help="Write the generated report to a text file"
    ),
):
    """Generates a Pulse insights summary using Gemini AI."""
    try:
        client = clients.setup_gemini_client(api_key, verbose)
        model = "gemini-2.0-flash"

        if verbose:
            console.print("[bold blue]reading[/] input file...")

        try:
            with open(details_json_file, "r") as f:
                input_data = json.load(f)
        except Exception as e:
            console.print(f"[bold red]error:[/] failed to read input file: {str(e)}")
            raise typer.Exit(1)

        try:
            repository = input_data["stats"]["repository"]
        except KeyError:
            console.print("[bold red]error:[/] missing 'repository' key in input file")
            raise typer.Exit(1)

        try:
            days_analyzed = input_data["stats"]["days_analyzed"]
        except KeyError:
            console.print(
                "[bold red]error:[/] missing 'days_analyzed' key in input file"
            )
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]generating[/] summary...")

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="text/plain",
        )

        response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=REPORT_PROMPT.format(
                repository=repository,
                days_analyzed=days_analyzed,
                input_data=input_data,
            ),
            config=generate_content_config,
        ):
            if stream:
                console.print(chunk.text, end="")
            response += chunk.text

        if not stream:
            console.print(response)

        if write:
            if verbose:
                console.print("[bold blue]writing[/] report to file...")
            fio.write_text_to_file(response, "pr-pulse-report", verbose)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
