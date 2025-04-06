from pathlib import Path

import typer
from rich.console import Console

from pr_pulse.core import clients, slack

app = typer.Typer(
    help="Share Pulse insights",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def slack(
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
        help="Slack webhook URL. if not provided, will try to use default config",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Shares Pulse insights on Slack."""
    try:
        webhook = clients.setup_slack_webhook_client(webhook_url, verbose)
        slack.share_report_to_slack(input_file, webhook, verbose)
    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
