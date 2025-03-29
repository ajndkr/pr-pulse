from pathlib import Path

import typer
from rich.console import Console
from slack_sdk.errors import SlackApiError

from pr_pulse import utils

app = typer.Typer()
console = Console()


@app.command()
def notify(
    input_file: Path = typer.Argument(
        ...,
        help="Path to input JSON file to read",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    webhook_url: str = typer.Option(
        None,
        help="Slack webhook URL. If not provided, will try to use SLACK_WEBHOOK_URL environment variable",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Sends PR Pulse report to Slack using blocks format."""
    try:
        webhook = utils.setup_slack_webhook_client(webhook_url, verbose)

        if verbose:
            console.print("[bold blue]reading[/] input file...")

        try:
            report = input_file.read_text()
        except Exception as e:
            console.print(f"[bold red]error:[/] failed to read input file: {str(e)}")
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]preparing[/] slack message...")

        blocks = utils.create_report_slack_blocks(report)

        if verbose:
            console.print("[bold blue]sending[/] message to Slack...")

        try:
            response = webhook.send(blocks=blocks)
            if response.status_code == 200:
                console.print("[bold green]success:[/] message sent to Slack")
            else:
                console.print(
                    f"[bold red]error:[/] failed to send message: {response.body}"
                )
                raise typer.Exit(1)
        except SlackApiError as e:
            console.print(f"[bold red]error:[/] Slack API error: {str(e)}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
