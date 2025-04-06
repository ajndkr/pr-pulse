import typer
from rich.console import Console

from pr_pulse.core import chains, clients, github, slack

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
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    days: int = typer.Option(7, help="Number of days to look back for PRs"),
    github_token: str = typer.Option(
        None,
        help="GitHub personal access token. If not provided, will try to use default config",
    ),
    api_key: str = typer.Option(
        None,
        help="GEMINI API key. If not provided, will try to use default config",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
    write: bool = typer.Option(
        False, "--write", "-w", help="Write the generated report to a text file"
    ),
    share: bool = typer.Option(
        False, "--share", help="Share the generated report to Slack"
    ),
    webhook_url: str = typer.Option(
        None,
        help="Slack webhook URL. If not provided, will try to use default config",
    ),
):
    """Generates a Pulse insights summary using Gemini AI."""
    try:
        repository, g = clients.setup_github_client(repo, github_token, verbose)
        pr_data = github.get_prs_details_data(repository, g, repo, days, verbose)

        gemini_client = clients.setup_gemini_client(api_key, verbose)
        report = chains.generate_pr_summary_from_data(
            pr_data=pr_data,
            llm=gemini_client,
            stream=stream,
            verbose=verbose,
            write=write,
        )

        if share:
            if verbose:
                console.print("[bold blue]sharing[/] report to Slack...")
            webhook = clients.setup_slack_webhook_client(webhook_url, verbose)
            slack_message = slack.create_report_text(report)

            try:
                response = webhook.send(text=slack_message)
                if response.status_code == 200:
                    console.print("[bold green]success:[/] message sent to Slack")
                else:
                    console.print(
                        f"[bold red]error:[/] failed to send message: {response.body}"
                    )
            except Exception as e:
                console.print(f"[bold red]error:[/] Slack API error: {str(e)}")
                raise e

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
