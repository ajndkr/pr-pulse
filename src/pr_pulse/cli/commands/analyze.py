from pathlib import Path

import typer
from rich.console import Console

from pr_pulse.core import chains, clients

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
        gemini_client = clients.setup_gemini_client(api_key, verbose)
        chains.generate_pr_summary(
            details_json_file=details_json_file,
            llm=gemini_client,
            stream=stream,
            verbose=verbose,
            write=write,
        )
    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
