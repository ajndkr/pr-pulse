import typer
import datetime
from github import Github, Auth
import os
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
import json
from enum import Enum
from github.Repository import Repository

app = typer.Typer(help="CLI tool for GitHub PR operations")
console = Console()


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


MAX_COMMENTS = 5


def setup_github_client(
    repo: str, token: str | None, verbose: bool
) -> tuple[Repository, Github]:
    """Sets up GitHub client and repository instance."""
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
        return repository, g
    except Exception as e:
        console.print(f"[bold red]error:[/] could not find repository {repo}: {str(e)}")
        raise typer.Exit(1)


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

        table = None
        if output_format.lower() == OutputFormat.table:
            if verbose:
                console.print("[bold blue]preparing[/] results table...")

            table = Table(title=f"merged PRs in {repo} (last {days} days)")
            table.add_column("pr #", justify="right", style="cyan")
            table.add_column("title", style="green")
            table.add_column("author", style="yellow")

        pr_data = []

        if verbose:
            console.print("[bold blue]processing[/] pull requests...")
        for pr in pulls:
            if table:
                table.add_row(str(pr.number), pr.title, pr.user.login, pr.html_url)
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

        try:
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

        comments = pr.get_issue_comments()
        comments_data = []
        comment_display_count = min(MAX_COMMENTS, comments.totalCount)

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
            "displayed_count": comment_display_count,
            "items": comments_data,
        }

        if output_format.lower() == OutputFormat.table:
            details_table = Table(title=f"PR #{pr.number} Details")
            details_table.add_column("field", style="cyan", justify="right")
            details_table.add_column("value", style="green")

            details_table.add_row("title", pr.title)
            details_table.add_row("author", pr.user.login)
            details_table.add_row(
                "status",
                "merged" if pr.merged else "open" if pr.state == "open" else "closed",
            )
            details_table.add_row(
                "created At", pr.created_at.strftime("%Y-%m-%d %H:%M")
            )
            if pr.merged:
                details_table.add_row(
                    "merged At", pr.merged_at.strftime("%Y-%m-%d %H:%M")
                )
            details_table.add_row("url", pr.html_url)

            console.print(details_table)

            if pr.body:
                desc_table = Table(title="description")
                desc_table.add_column("content", style="yellow")
                desc_table.add_row(pr.body)
                console.print("\n")
                console.print(desc_table)
            else:
                console.print("\n[italic]no description provided[/]")

            if comments.totalCount > 0:
                comments_table = Table(
                    title=f"comments (showing {comment_display_count} of {comments.totalCount})"
                )
                comments_table.add_column("author", style="cyan")
                comments_table.add_column("date", style="yellow")
                comments_table.add_column("comment", style="green")

                for comment in comments[:5]:
                    comments_table.add_row(
                        comment.user.login,
                        comment.created_at.strftime("%Y-%m-%d %H:%M"),
                        comment.body,
                    )

                console.print("\n")
                console.print(comments_table)
            else:
                console.print("\n[italic]no comments found[/]")
        else:
            print(json.dumps(pr_data))

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
