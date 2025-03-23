import typer
import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
import json
import asyncio

from pr_pulse.utils import (
    setup_github_client,
    search_merged_pull_requests,
    get_pr_details,
    get_pr_details_batch,
    display_pr_details_table,
    format_pr_data,
)

from pr_pulse.constants import OutputFormat

app = typer.Typer(help="CLI tool for GitHub PR operations")
console = Console()


@app.command()
def list(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    days: int = typer.Option(7, help="number of days to look back for PRs"),
    token: str = typer.Option(
        None,
        help="GitHub personal access token. if not provided, will try to use GITHUB_TOKEN environment variable",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="output format",
        show_choices=True,
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Lists all merged pull requests for a repository within the specified time frame."""
    try:
        _, g = setup_github_client(repo, token, verbose)
        pulls = search_merged_pull_requests(g, repo, days, verbose)

        table = None
        if output_format.lower() == OutputFormat.table:
            if verbose:
                console.print("[bold blue]preparing[/] results table...")

            table = Table(title=f"merged PRs in {repo} (last {days} days)")
            table.add_column("#", justify="right", style="cyan")
            table.add_column("title", style="green")
            table.add_column("author", style="yellow")

        pr_data = []

        if verbose:
            console.print("[bold blue]processing[/] pull requests...")
        for pr in pulls:
            if table:
                table.add_row(str(pr.number), pr.title, pr.user.login)
            else:
                pr_data.append(
                    dict(number=pr.number, title=pr.title, author=pr.user.login)
                )

        if table:
            console.print(table)
        else:
            result = dict(
                repository=repo,
                days_searched=days,
                total_prs=len(pr_data),
                pull_requests=pr_data,
            )
            print(json.dumps(result))

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)


@app.command()
def detail(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    token: str = typer.Option(
        None,
        help="GitHub personal access token. If not provided, will try to use GITHUB_TOKEN environment variable",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="output format",
        show_choices=True,
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Shows details of a specific pull request including summary and top comments."""
    try:
        repository, _ = setup_github_client(repo, token, verbose)
        pr = get_pr_details(repository, pr_number, verbose)

        if verbose:
            console.print("[bold blue]preparing[/] pr details...")

        if output_format.lower() == OutputFormat.table:
            display_pr_details_table(pr)
        else:
            pr_data = format_pr_data(pr)
            print(json.dumps(pr_data))

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)


@app.command()
def summary(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    days: int = typer.Option(7, help="number of days to look back for PRs"),
    token: str = typer.Option(
        None,
        help="GitHub personal access token. if not provided, will try to use GITHUB_TOKEN environment variable",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="output format",
        show_choices=True,
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Provides a summary of all merged pull requests with their details."""
    try:
        repository, g = setup_github_client(repo, token, verbose)
        pulls = search_merged_pull_requests(g, repo, days, verbose)

        if verbose:
            console.print("[bold blue]fetching[/] details for each PR...")

        pr_numbers = [pull.number for pull in pulls]
        pr_count = len(pr_numbers)

        pr_details = asyncio.run(get_pr_details_batch(repository, pr_numbers, verbose))

        if output_format.lower() == OutputFormat.table:
            summary_table = Table(title=f"PR summary for {repo} (last {days} days)")
            summary_table.add_column("#", style="cyan", justify="right")
            summary_table.add_column("title", style="green")
            summary_table.add_column("author", style="yellow")
            summary_table.add_column("merged at", style="magenta")

            for pr in pr_details:
                summary_table.add_row(
                    str(pr.number),
                    pr.title,
                    pr.user.login,
                    pr.merged_at.strftime("%Y-%m-%d %H:%M")
                    if pr.merged
                    else "Not merged",
                )

            console.print(summary_table)
            console.print(f"\n[bold]total PRs:[/] {pr_count}")

            for pr in pr_details:
                console.print(f"\n[bold]===== PR #{pr.number}: {pr.title} =====\n[/]")
                if pr.body:
                    # escape any Rich markup in PR body to prevent rendering errors
                    safe_body = pr.body.replace("[", "\\[").replace("]", "\\]")
                    desc_table = Table(title=f"PR #{pr.number} Description")
                    desc_table.add_column("Content", style="yellow")
                    desc_table.add_row(safe_body)
                    console.print(desc_table)
                else:
                    console.print("[italic]no description provided[/]")
        else:
            stats = dict(
                repository=repo,
                days_analyzed=days,
                total_prs=pr_count,
                date_range=dict(
                    end=datetime.datetime.now().strftime("%Y-%m-%d"),
                    start=(
                        datetime.datetime.now() - datetime.timedelta(days=days)
                    ).strftime("%Y-%m-%d"),
                ),
            )
            formatted_prs = [
                format_pr_data(pr, include_comments=True) for pr in pr_details
            ]
            output = dict(stats=stats, pull_requests=formatted_prs)

            print(json.dumps(output))

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """CLI Entrypoint"""
    load_dotenv()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
