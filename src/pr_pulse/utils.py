import asyncio
import datetime
import os
import pathlib
from typing import List

import typer
from github import Auth, Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from google import genai
from rich.console import Console
from rich.table import Table
from slack_sdk.webhook import WebhookClient

from pr_pulse.constants import BATCH_SIZE, MAX_COMMENTS

console = Console()


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


def search_merged_pull_requests(g: Github, repo: str, days: int, verbose: bool):
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
    repository: Repository, pr_number: int, verbose: bool
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
    repository: Repository, pr_numbers: List[int], verbose: bool
) -> List[PullRequest]:
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


def write_json_to_file(
    data: dict, prefix: str = "pr-pulse", verbose: bool = False
) -> None:
    """Writes JSON data to a file."""
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    filename = f"{prefix}-{today}.json"
    output_path = pathlib.Path(filename)
    output_path.write_text(data)
    if verbose:
        console.print(f"[green]results written to:[/] {filename}")


def write_text_to_file(
    text: str, prefix: str = "pr-pulse", verbose: bool = False
) -> None:
    """Writes text data to a file."""
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    filename = f"{prefix}-{today}.txt"
    output_path = pathlib.Path(filename)
    output_path.write_text(text)
    if verbose:
        console.print(f"[green]results written to:[/] {filename}")


def setup_gemini_client(api_key: str | None, verbose: bool) -> genai.Client:
    """Sets up Gemini client."""
    api_key = api_key or os.environ.get("GENAI_API_KEY")
    if not api_key:
        console.print("[bold red]error:[/] GENAI_API_KEY environment variable not set")
        raise typer.Exit(1)

    if verbose:
        console.print("[bold blue]initializing[/] Gemini AI client...")

    return genai.Client(api_key=api_key)


def setup_slack_webhook_client(webhook_url: str | None, verbose: bool) -> WebhookClient:
    """Sets up Slack webhook client."""
    webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        console.print(
            "[bold red]error:[/] Slack webhook URL not provided and SLACK_WEBHOOK_URL environment variable not set"
        )
        raise typer.Exit(1)

    if verbose:
        console.print("[bold blue]initializing[/] Slack client...")

    return WebhookClient(webhook_url)


def create_report_slack_blocks(report: str):
    """Creates Slack blocks from report."""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*PR Pulse Report*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": report,
            },
        },
    ]

    return blocks
