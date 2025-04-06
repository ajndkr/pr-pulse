import json

import typer
from rich.console import Console

from pr_pulse.constants import OutputFormat
from pr_pulse.core import clients, fio, github

app = typer.Typer(
    help="Get PR data from GitHub",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def list(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    days: int = typer.Option(7, help="number of days to look back for PRs"),
    token: str = typer.Option(
        None,
        help="GitHub personal access token. if not provided, will try to use default config",
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
    """Get list of merged pull requests within the specified time frame."""
    try:
        _, g = clients.setup_github_client(repo, token, verbose)

        result, pulls = github.get_pr_list_data(g, repo, days, verbose)

        if output_format.lower() == OutputFormat.table:
            github.display_pr_list_table(pulls, repo, days)
        else:
            json_output = json.dumps(result)
            print(json_output)

            if write:
                fio.write_json_to_file(json_output, "pr-pulse-list", verbose)

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
    """Get pull request details including description and comments."""
    try:
        repository, _ = clients.setup_github_client(repo, token, verbose)

        pr_data, pr = github.get_pr_detail_data(repository, pr_number, verbose)

        if output_format.lower() == OutputFormat.table:
            github.display_pr_details_table(pr)
        else:
            json_output = json.dumps(pr_data)
            print(json_output)

            if write:
                fio.write_json_to_file(json_output, "pr-pulse-detail", verbose)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)


@app.command()
def details(
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
    """Get details of all merged pull requests within the specified time frame."""
    try:
        repository, g = clients.setup_github_client(repo, token, verbose)

        result = github.get_prs_details_data(repository, g, repo, days, verbose)

        if output_format.lower() == OutputFormat.table:
            github.display_pr_details_summary_table(result["pr_details"], repo, days)
        else:
            # Exclude the pr_details key which contains the actual PR objects
            output = {
                "stats": result["stats"],
                "pull_requests": result["pull_requests"],
            }
            json_output = json.dumps(output)

            if write:
                fio.write_json_to_file(json_output, "pr-pulse-summary", verbose)

            print(json_output)

    except Exception as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
