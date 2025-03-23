import typer
import datetime
from github import Github, Auth
import os
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
import json
from enum import Enum

app = typer.Typer(help="CLI tool for GitHub PR operations")
console = Console()


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


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
        github_token = token or os.environ.get("GITHUB_TOKEN")
        if not github_token:
            console.print(
                "[bold red]error:[/] GitHub token not provided and GITHUB_TOKEN environment variable not set"
            )
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]authenticating[/] with github...")
        auth = Auth.Token(github_token)
        g = Github(auth=auth)

        try:
            if verbose:
                console.print(f"[bold blue]connecting[/] to repository {repo}...")
            repository = g.get_repo(repo)
        except Exception as e:
            console.print(
                f"[bold red]error:[/] could not find repository {repo}: {str(e)}"
            )
            raise typer.Exit(1)

        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        if verbose:
            console.print(
                f"[bold blue]searching[/] PRs from the last {days} days (until {end_date.strftime('%Y-%m-%d')})"
            )

        query = (
            f"repo:{repo} is:pr is:merged merged:>={start_date.strftime('%Y-%m-%d')}"
        )

        if verbose:
            console.print("[bold blue]searching[/] for merged pull requests...")
        try:
            pulls = g.search_issues(query)
            if verbose:
                console.print(f"[bold blue]found[/] {pulls.totalCount} pull requests")
        except Exception as e:
            console.print(f"[bold red]error:[/] query failed: {str(e)}")
            console.print("[bold yellow]debugging info:[/]")
            console.print(f"- repository: {repo}")
            console.print(f"- query: {query}")
            raise typer.Exit(1)

        if output_format.lower() == OutputFormat.table:
            if verbose:
                console.print("[bold blue]preparing[/] results table...")

            table = Table(title=f"merged PRs in {repo} (last {days} days)")
            table.add_column("pr #", justify="right", style="cyan")
            table.add_column("title", style="green")
            table.add_column("author", style="yellow")
            table.add_column("merged at", style="magenta")

        pr_data = []

        if verbose:
            console.print("[bold blue]fetching[/] details for each pull request...")
        pr_count = 0
        for pr in pulls:
            pr_count += 1
            if verbose and pr_count % 5 == 0:
                console.print(
                    f"[bold blue]processing[/] pr #{pr.number} ({pr_count}/{pulls.totalCount})..."
                )
            try:
                pull_request = repository.get_pull(pr.number)
                if pull_request.merged_at:
                    merged_at = pull_request.merged_at.strftime("%Y-%m-%d %H:%M")
                    if output_format.lower() == OutputFormat.table:
                        table.add_row(
                            str(pr.number), pr.title, pr.user.login, merged_at
                        )
                    else:
                        pr_data.append(
                            {
                                "number": pr.number,
                                "title": pr.title,
                                "author": pr.user.login,
                                "merged_at": merged_at,
                            }
                        )
            except Exception as e:
                if verbose:
                    console.print(
                        f"[bold red]error:[/] failed to fetch PR #{pr.number}: {str(e)}"
                    )
                pr_data.append(
                    {
                        "number": pr.number,
                        "title": pr.title,
                        "author": pr.user.login,
                        "error": str(e),
                    }
                )
                continue

        if verbose:
            console.print("[bold blue]completed![/] displaying results:")

        if output_format.lower() == OutputFormat.table:
            console.print(table)
        else:
            result = {
                "repository": repo,
                "days_searched": days,
                "total_prs": len(pr_data),
                "pull_requests": pr_data,
            }
            print(json.dumps(result, indent=2))

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
        github_token = token or os.environ.get("GITHUB_TOKEN")
        if not github_token:
            console.print(
                "[bold red]error:[/] GitHub token not provided and GITHUB_TOKEN environment variable not set"
            )
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]authenticating[/] with github...")
        auth = Auth.Token(github_token)
        g = Github(auth=auth)

        try:
            if verbose:
                console.print(f"[bold blue]connecting[/] to repository {repo}...")
            repository = g.get_repo(repo)
            if verbose:
                console.print(f"[bold blue]fetching[/] pr #{pr_number}...")
            pr = repository.get_pull(pr_number)
        except Exception as e:
            console.print(
                f"[bold red]error:[/] could not find pr #{pr_number} in repository {repo}: {str(e)}"
            )
            raise typer.Exit(1)

        if verbose:
            console.print("[bold blue]preparing[/] pr details...")

        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "status": "merged"
            if pr.merged
            else "open"
            if pr.state == "open"
            else "closed",
            "created_at": pr.created_at.strftime("%Y-%m-%d %H:%M"),
            "url": pr.html_url,
            "description": pr.body or "",
        }

        if pr.merged:
            pr_data["merged_at"] = pr.merged_at.strftime("%Y-%m-%d %H:%M")

        if verbose:
            console.print("\n[bold blue]fetching[/] pr comments...")
        comments = pr.get_issue_comments()
        comments_data = []

        for i, comment in enumerate(comments[:5]):
            comments_data.append(
                {
                    "author": comment.user.login,
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
                    "body": comment.body,
                }
            )

        pr_data["comments"] = {
            "total_count": comments.totalCount,
            "displayed_count": min(5, comments.totalCount),
            "items": comments_data,
        }

        if output_format.lower() == OutputFormat.table:
            console.print(f"[bold cyan]pr #{pr.number}:[/] [bold green]{pr.title}[/]")
            console.print(f"[bold]author:[/] {pr.user.login}")
            console.print(
                f"[bold]status:[/] {'merged' if pr.merged else 'open' if pr.state == 'open' else 'closed'}"
            )
            if pr.merged:
                console.print(
                    f"[bold]merged at:[/] {pr.merged_at.strftime('%Y-%m-%d %H:%M')}"
                )
            console.print(
                f"[bold]created at:[/] {pr.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
            console.print(f"[bold]url:[/] {pr.html_url}")

            console.print("\n[bold]description:[/]")
            console.print(pr.body or "[italic]no description provided[/]")

            console.print("\n[bold]top comments:[/]")
            if comments.totalCount == 0:
                console.print("[italic]no comments found[/]")
            else:
                if verbose:
                    console.print(f"[bold blue]found[/] {comments.totalCount} comments")
                for i, comment in enumerate(comments[:5]):
                    if i == 0 and verbose:
                        console.print("[bold blue]displaying[/] top comments...")
                    console.print(
                        f"\n[bold yellow]{comment.user.login}[/] at {comment.created_at.strftime('%Y-%m-%d %H:%M')}:"
                    )
                    console.print(comment.body)

                if comments.totalCount > 5:
                    console.print(
                        f"\n[italic]...and {comments.totalCount - 5} more comments[/]"
                    )

            if verbose:
                console.print("\n[bold blue]completed![/] pr details displayed.")

        else:  # json format
            if verbose:
                console.print("[bold blue]generating[/] json output...")
            print(json.dumps(pr_data, indent=2))

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
