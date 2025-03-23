import typer
import datetime
from rich.console import Console
from rich.table import Table
import json
import asyncio

from pr_pulse import utils
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
    """Lists all merged pull requests for a repository within the specified time frame."""
    try:
        _, g = utils.setup_github_client(repo, token, verbose)
        pulls = utils.search_merged_pull_requests(g, repo, days, verbose)

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
            json_output = json.dumps(result)

            if write:
                utils.write_json_to_file(json_output, "pr-pulse-list", verbose)

            print(json_output)

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
    """Shows details of a specific pull request including summary and top comments."""
    try:
        repository, _ = utils.setup_github_client(repo, token, verbose)
        pr = utils.get_pr_details(repository, pr_number, verbose)

        if verbose:
            console.print("[bold blue]preparing[/] pr details...")

        if output_format.lower() == OutputFormat.table:
            utils.display_pr_details_table(pr)
        else:
            pr_data = utils.format_pr_data(pr)
            json_output = json.dumps(pr_data)

            if write:
                utils.write_json_to_file(json_output, "pr-pulse-detail", verbose)

            print(json_output)

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
    """Provides a summary of all merged pull requests with their details."""
    try:
        repository, g = utils.setup_github_client(repo, token, verbose)
        pulls = utils.search_merged_pull_requests(g, repo, days, verbose)

        if verbose:
            console.print("[bold blue]fetching[/] details for each PR...")

        pr_numbers = [pull.number for pull in pulls]
        pr_count = len(pr_numbers)

        pr_details = asyncio.run(
            utils.get_pr_details_batch(repository, pr_numbers, verbose)
        )

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
                utils.format_pr_data(pr, include_comments=True) for pr in pr_details
            ]
            output = dict(stats=stats, pull_requests=formatted_prs)
            json_output = json.dumps(output)

            if write:
                utils.write_json_to_file(json_output, "pr-pulse-summary", verbose)

            print(json_output)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
