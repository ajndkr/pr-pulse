import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pr_pulse import utils
from pr_pulse.constants import REPORT_PROMPT, OutputFormat

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
        help="GEMINI API key. if not provided, will try to use GEMINI_API_KEY environment variable",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="Output format",
        show_choices=True,
        case_sensitive=False,
    ),
    write: bool = typer.Option(
        False,
        "--write",
        "-w",
        help="Write JSON output to a file (only used with JSON format)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
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
            if verbose:
                console.print(chunk.text, end="")
            response += chunk.text

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            console.print("[bold red]error:[/] failed to parse AI response as JSON")
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]processing[/] results...")

        if output_format.lower() == OutputFormat.table:
            summary_table = Table(title="pr summary report")
            summary_table.add_column("summary", style="green")
            summary_table.add_row(result.get("summary", "no summary generated"))
            console.print(summary_table)

            details_table = Table(title="functional requirements")
            details_table.add_column("details", style="yellow")
            details_table.add_row(result.get("details", "no details generated"))
            console.print(details_table)
        else:
            json_output = json.dumps(result)

            if write:
                utils.write_json_to_file(json_output, "pr-pulse-ai-report", verbose)

            print(json_output)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
