import asyncio
import datetime

import typer
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from rich.console import Console
from rich.table import Table

from pr_pulse.config import get_config
from pr_pulse.constants import BATCH_SIZE, MAX_COMMENTS

console = Console()


def search_merged_pull_requests(
    g: Github, repo: str, days: int, verbose: bool = get_config().verbose
):
    """Searches for merged pull requests in a repository within the specified time frame."""
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)

    if verbose:
        console.print(
            f"[bold blue]searching[/] PRs from the last {days} days (until {end_date.strftime('%Y-%m-%d')})"
        )

    query = f"repo:{repo} is:pr is:merged merged:>={start_date.strftime('%Y-%m-%d')}"

    if verbose:
        console.print("[bold blue]searching[/] for merged pull requests...")
    try:
        pulls = g.search_issues(query)
        if verbose:
            console.print(f"[bold blue]found[/] {pulls.totalCount} pull requests")
        return pulls
    except Exception as e:
        console.print(f"[bold red]error:[/] query failed: {str(e)}")
        console.print("[bold yellow]debugging info:[/]")
        console.print(f"- repository: {repo}")
        console.print(f"- query: {query}")
        raise typer.Exit(1)


def get_pr_details(
    repository: Repository, pr_number: int, verbose: bool = get_config().verbose
) -> PullRequest:
    """Fetches details of a specific pull request."""
    try:
        if verbose:
            console.print(f"[bold blue]fetching[/] pr #{pr_number}...")
        return repository.get_pull(pr_number)
    except Exception as e:
        console.print(
            f"[bold red]error:[/] could not find pr #{pr_number} in repository {repository.full_name}: {str(e)}"
        )
        raise typer.Exit(1)


async def get_pr_details_batch(
    repository: Repository, pr_numbers: list[int], verbose: bool = get_config().verbose
) -> list[PullRequest]:
    """Fetches details of pull requests in a batch."""
    results = []

    for i in range(0, len(pr_numbers), BATCH_SIZE):
        batch = pr_numbers[i : i + BATCH_SIZE]
        batch_tasks = [
            asyncio.to_thread(get_pr_details, repository, pr_num, verbose)
            for pr_num in batch
        ]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)

    return results


def format_pr_data(pr: PullRequest, include_comments: bool = True) -> dict:
    """Formats pull request data into a dictionary."""
    pr_data = dict(
        number=pr.number,
        title=pr.title,
        author=pr.user.login,
        status="merged" if pr.merged else "open" if pr.state == "open" else "closed",
        created_at=pr.created_at.strftime("%Y-%m-%d %H:%M"),
        url=pr.html_url,
        description=pr.body or "",
    )

    if pr.merged:
        pr_data["merged_at"] = pr.merged_at.strftime("%Y-%m-%d %H:%M")

    if include_comments:
        comments = pr.get_issue_comments()
        comments_data = []
        comment_display_count = min(MAX_COMMENTS, comments.totalCount)

        # only try to iterate through comments if there are any
        if comments.totalCount > 0:
            for comment in comments[:5]:
                comments_data.append(
                    dict(
                        author=comment.user.login,
                        created_at=comment.created_at.strftime("%Y-%m-%d %H:%M"),
                        body=comment.body,
                    )
                )

        pr_data["comments"] = dict(
            total_count=comments.totalCount,
            displayed_count=comment_display_count,
            items=comments_data,
        )

    return pr_data


def display_pr_details_table(pr: PullRequest, show_comments: bool = True):
    """Displays pull request details in table format (comments are optional)."""
    details_table = Table(title=f"pr #{pr.number} details")
    details_table.add_column("field", style="cyan", justify="right")
    details_table.add_column("value", style="green")

    details_table.add_row("title", pr.title)
    details_table.add_row("author", pr.user.login)
    details_table.add_row(
        "status",
        "merged" if pr.merged else "open" if pr.state == "open" else "closed",
    )
    details_table.add_row("created at", pr.created_at.strftime("%Y-%m-%d %H:%M"))
    if pr.merged:
        details_table.add_row("merged at", pr.merged_at.strftime("%Y-%m-%d %H:%M"))
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

    if show_comments:
        comments = pr.get_issue_comments()
        if comments.totalCount > 0:
            comment_display_count = min(MAX_COMMENTS, comments.totalCount)
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
