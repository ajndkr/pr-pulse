import asyncio
import datetime
from typing import Any

import typer
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from rich.console import Console
from rich.table import Table

from pr_pulse.config import get_config
from pr_pulse.constants import BATCH_SIZE, MAX_COMMENTS

console = Console()


def get_date_range(days: int) -> tuple[datetime.datetime, datetime.datetime]:
    """Gets start and end dates for a time range."""
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    return start_date, end_date


def format_date(date: datetime.datetime) -> str:
    """Formats a datetime object to a standard string format."""
    return date.strftime("%Y-%m-%d %H:%M")


def format_date_ymd(date: datetime.datetime) -> str:
    """Formats a datetime object to YYYY-MM-DD format."""
    return date.strftime("%Y-%m-%d")


def search_merged_pull_requests(
    g: Github, repo: str, days: int, verbose: bool = get_config().verbose
):
    """Searches for merged pull requests in a repository within the specified time frame."""
    start_date, end_date = get_date_range(days)

    if verbose:
        console.print(
            f"[bold blue]searching[/] PRs from the last {days} days (until {format_date_ymd(end_date)})"
        )

    query = f"repo:{repo} is:pr is:merged merged:>={format_date_ymd(start_date)}"

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


def format_pr_data(pr: PullRequest, include_comments: bool = True) -> dict[str, Any]:
    """Formats pull request data into a dictionary."""
    pr_data = dict(
        number=pr.number,
        title=pr.title,
        author=pr.user.login,
        status="merged" if pr.merged else "open" if pr.state == "open" else "closed",
        created_at=format_date(pr.created_at),
        url=pr.html_url,
        description=pr.body or "",
    )

    if pr.merged:
        pr_data["merged_at"] = format_date(pr.merged_at)

    if include_comments:
        comments = pr.get_issue_comments()
        comments_data = []
        comment_display_count = min(MAX_COMMENTS, comments.totalCount)

        # only try to iterate through comments if there are any
        if comments.totalCount > 0:
            for comment in comments[:MAX_COMMENTS]:
                comments_data.append(
                    dict(
                        author=comment.user.login,
                        created_at=format_date(comment.created_at),
                        body=comment.body,
                    )
                )

        pr_data["comments"] = dict(
            total_count=comments.totalCount,
            displayed_count=comment_display_count,
            items=comments_data,
        )

    return pr_data


def get_pr_list_data(
    g: Github, repo: str, days: int, verbose: bool = False
) -> tuple[dict[str, Any], Any]:
    """Gets list of merged pull requests data within the specified time frame."""
    pulls = search_merged_pull_requests(g, repo, days, verbose)
    pr_data = []

    if verbose:
        console.print("[bold blue]processing[/] pull requests...")

    for pr in pulls:
        pr_data.append(dict(number=pr.number, title=pr.title, author=pr.user.login))

    result = dict(
        repository=repo,
        days_searched=days,
        total_prs=len(pr_data),
        pull_requests=pr_data,
    )

    return result, pulls


def display_pr_list_table(pulls, repo: str, days: int):
    """Displays PR list in table format."""
    table = Table(title=f"merged PRs in {repo} (last {days} days)")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("title", style="green")
    table.add_column("author", style="yellow")

    for pr in pulls:
        table.add_row(str(pr.number), pr.title, pr.user.login)

    console.print(table)


def get_pr_detail_data(repository: Repository, pr_number: int, verbose: bool = False):
    """Gets details for a single pull request."""
    pr = get_pr_details(repository, pr_number, verbose)
    pr_data = format_pr_data(pr, include_comments=True)
    return pr_data, pr


def escape_rich_markup(text: str) -> str:
    """Escapes Rich markup in text to prevent rendering errors."""
    if not text:
        return ""
    return text.replace("[", "\\[").replace("]", "\\]")


def display_description(body: str, title: str = "description"):
    """Displays a PR description in a table."""
    if not body:
        console.print("\n[italic]no description provided[/]")
        return

    desc_table = Table(title=title)
    desc_table.add_column("content", style="yellow")
    desc_table.add_row(escape_rich_markup(body))
    console.print("\n")
    console.print(desc_table)


def display_comments(comments, max_comments: int = MAX_COMMENTS):
    """Displays comments in a table."""
    if comments.totalCount == 0:
        console.print("\n[italic]no comments found[/]")
        return

    comment_display_count = min(max_comments, comments.totalCount)
    comments_table = Table(
        title=f"comments (showing {comment_display_count} of {comments.totalCount})"
    )
    comments_table.add_column("author", style="cyan")
    comments_table.add_column("date", style="yellow")
    comments_table.add_column("comment", style="green")

    for comment in comments[:max_comments]:
        comments_table.add_row(
            comment.user.login,
            format_date(comment.created_at),
            comment.body,
        )

    console.print("\n")
    console.print(comments_table)


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
    details_table.add_row("created at", format_date(pr.created_at))
    if pr.merged:
        details_table.add_row("merged at", format_date(pr.merged_at))
    details_table.add_row("url", pr.html_url)

    console.print(details_table)
    display_description(pr.body)

    if show_comments:
        display_comments(pr.get_issue_comments())


def get_prs_details_data(
    repository: Repository, g: Github, repo: str, days: int, verbose: bool = False
) -> dict[str, Any]:
    """Gets details for multiple pull requests within a time frame."""
    pulls = search_merged_pull_requests(g, repo, days, verbose)

    if verbose:
        console.print("[bold blue]fetching[/] details for each PR...")

    pr_numbers = [pull.number for pull in pulls]
    pr_count = len(pr_numbers)

    pr_details = asyncio.run(get_pr_details_batch(repository, pr_numbers, verbose))

    start_date, end_date = get_date_range(days)
    stats = dict(
        repository=repo,
        days_analyzed=days,
        total_prs=pr_count,
        date_range=dict(
            end=format_date_ymd(end_date),
            start=format_date_ymd(start_date),
        ),
    )

    formatted_prs = [format_pr_data(pr, include_comments=True) for pr in pr_details]

    return {"stats": stats, "pull_requests": formatted_prs, "pr_details": pr_details}


def display_pr_details_summary_table(pr_details, repo: str, days: int):
    """Displays summary table for multiple PR details."""
    pr_count = len(pr_details)
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
            format_date(pr.merged_at) if pr.merged else "Not merged",
        )

    console.print(summary_table)
    console.print(f"\n[bold]total PRs:[/] {pr_count}")

    for pr in pr_details:
        console.print(f"\n[bold]===== PR #{pr.number}: {pr.title} =====\n[/]")
        display_description(pr.body, title=f"PR #{pr.number} Description")
