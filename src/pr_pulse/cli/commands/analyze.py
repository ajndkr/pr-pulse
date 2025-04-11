import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from pr_pulse.core import clients
from pr_pulse.core.chains import generate_pr_summary_from_data
from pr_pulse.core.clients import ClientError
from pr_pulse.core.slack import create_report_text

app = typer.Typer(
    help="Analyze PR data and generate Pulse insights",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


class SlackError(Exception):
    """Exception raised for Slack API errors"""

    pass


@app.command()
def summary(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    days: int = typer.Option(7, help="Number of days to look back for PRs"),
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
):
    """Generates a Pulse insights summary using Gemini AI"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            transient=True,
            disable=not verbose,
        ) as progress:
            task = progress.add_task("Setting up GitHub client...", total=None)
            github_repo, _, _ = clients.setup_github_client(repo, verbose)

            progress.update(task, description="Fetching PR details...")
            pr_data = github_repo.get_prs_details_data(repo, days)

            progress.update(task, description="Setting up Gemini client...")
            gemini_client = clients.setup_gemini_client(verbose)

            progress.update(task, description="Generating insights summary...")
            report = generate_pr_summary_from_data(
                pr_data=pr_data,
                llm=gemini_client,
                stream=stream,
                verbose=verbose,
                write=write,
            )

            if share:
                progress.update(task, description="Sharing report to Slack...")
                webhook = clients.setup_slack_webhook_client(verbose)
                slack_message = create_report_text(report)

                try:
                    response = webhook.send(text=slack_message)
                    if response.status_code == 200:
                        console.print("[bold green]success:[/] message sent to Slack")
                    else:
                        raise SlackError(f"Failed to send message: {response.body}")
                except Exception as e:
                    console.print(f"[bold red]error:[/] Slack API error: {str(e)}")
                    raise SlackError(f"Slack API error: {str(e)}")

    except ClientError as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
    except SlackError as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]unexpected error:[/] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
