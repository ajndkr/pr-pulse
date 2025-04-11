import json

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from pr_pulse.constants import OutputFormat
from pr_pulse.core import github
from pr_pulse.core.clients import ClientError, setup_github_client
from pr_pulse.core.io import write_json_to_file

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
        help="Write JSON output to a file (pass '-f json' to enable)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Get list of merged pull requests over the past specified number of days"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            transient=True,
            disable=not verbose,
        ) as progress:
            task = progress.add_task("Setting up GitHub client...", total=None)
            github_repo, _, _ = setup_github_client(repo, verbose)

            progress.update(task, description="Fetching PR list...")
            result, pulls = github_repo.get_pr_list_data(repo, days)

            if output_format.lower() == OutputFormat.table:
                github.display_pr_list_table(pulls, repo, days)
            else:
                json_output = result.json()
                print(json_output)

                if write:
                    write_json_to_file(json_output, "pr-pulse-list", verbose)

    except ClientError as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]unexpected error:[/] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def detail(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
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
        help="Write JSON output to a file (pass '-f json' to enable)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Get pull request details including description and comments over the past specified number of days"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            transient=True,
            disable=not verbose,
        ) as progress:
            task = progress.add_task("Setting up GitHub client...", total=None)
            github_repo, repository, _ = setup_github_client(repo, verbose)

            progress.update(task, description=f"Fetching PR #{pr_number}...")
            pr_data, pr = github_repo.get_pr_detail_data(pr_number)

            if output_format.lower() == OutputFormat.table:
                github.display_pr_details_table(pr)
            else:
                json_output = json.dumps(pr_data)
                print(json_output)

                if write:
                    write_json_to_file(json_output, "pr-pulse-detail", verbose)

    except ClientError as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]unexpected error:[/] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def details(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    days: int = typer.Option(7, help="number of days to look back for PRs"),
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
        help="Write JSON output to a file (pass '-f json' to enable)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress logs"
    ),
):
    """Get details of all merged pull requests over the past specified number of days"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            transient=True,
            disable=not verbose,
        ) as progress:
            task = progress.add_task("Setting up GitHub client...", total=None)
            github_repo, repository, g = setup_github_client(repo, verbose)

            progress.update(task, description="Fetching PR details...")
            result = github_repo.get_prs_details_data(repo, days)

            if output_format.lower() == OutputFormat.table:
                github.display_pr_details_summary_table(
                    result["pr_details"], repo, days
                )
            else:
                # Exclude the pr_details key which contains the actual PR objects
                output = {
                    "stats": result["stats"],
                    "pull_requests": result["pull_requests"],
                }
                json_output = json.dumps(output)

                if write:
                    write_json_to_file(json_output, "pr-pulse-summary", verbose)

                print(json_output)

    except ClientError as e:
        console.print(f"[bold red]error:[/] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]unexpected error:[/] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
