import asyncio
import datetime
from typing import Any, Dict, List, Tuple

from github import Github
from github.PullRequest import PullRequest as GithubPullRequest
from github.Repository import Repository

from pr_pulse.constants import BATCH_SIZE, MAX_COMMENTS
from pr_pulse.models import Comment, DateRange, PRListResponse, PullRequest, Stats


class GitHubRepository:
    def __init__(
        self, github_client: Github, repository: Repository, verbose: bool = False
    ):
        self.github_client = github_client
        self.repository = repository
        self.verbose = verbose

    def get_date_range(self, days: int) -> Tuple[datetime.datetime, datetime.datetime]:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        return start_date, end_date

    def format_date(self, date: datetime.datetime) -> str:
        return date.strftime("%Y-%m-%d %H:%M")

    def format_date_ymd(self, date: datetime.datetime) -> str:
        return date.strftime("%Y-%m-%d")

    def search_merged_pull_requests(self, repo: str, days: int):
        start_date, end_date = self.get_date_range(days)
        query = (
            f"repo:{repo} is:pr is:merged merged:>={self.format_date_ymd(start_date)}"
        )
        return self.github_client.search_issues(query)

    def get_pr_details(self, pr_number: int) -> GithubPullRequest:
        return self.repository.get_pull(pr_number)

    async def get_pr_details_batch(
        self, pr_numbers: List[int]
    ) -> List[GithubPullRequest]:
        results = []

        for i in range(0, len(pr_numbers), BATCH_SIZE):
            batch = pr_numbers[i : i + BATCH_SIZE]
            batch_tasks = [
                asyncio.to_thread(self.get_pr_details, pr_num) for pr_num in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

        return results

    def format_pr_data(
        self, pr: GithubPullRequest, include_comments: bool = True
    ) -> PullRequest:
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "status": "merged"
            if pr.merged
            else "open"
            if pr.state == "open"
            else "closed",
            "created_at": self.format_date(pr.created_at),
            "url": pr.html_url,
            "description": pr.body or "",
        }

        if pr.merged:
            pr_data["merged_at"] = self.format_date(pr.merged_at)

        if include_comments:
            comments = pr.get_issue_comments()
            comments_data = []

            if comments.totalCount > 0:
                for comment in comments[:MAX_COMMENTS]:
                    comments_data.append(
                        Comment(
                            author=comment.user.login,
                            created_at=self.format_date(comment.created_at),
                            body=comment.body,
                        )
                    )

                pr_data["comments"] = comments_data

        return PullRequest(**pr_data)

    def get_pr_list_data(
        self, repo: str, days: int
    ) -> Tuple[PRListResponse, List[Any]]:
        pulls = self.search_merged_pull_requests(repo, days)

        start_date, end_date = self.get_date_range(days)
        stats = Stats(
            repository=repo,
            days_analyzed=days,
            total_prs=pulls.totalCount,
            date_range=DateRange(
                start=self.format_date_ymd(start_date),
                end=self.format_date_ymd(end_date),
            ),
        )

        pull_requests = []
        for pull in pulls:
            pr = self.get_pr_details(pull.number)
            pull_requests.append(self.format_pr_data(pr, include_comments=False))

        response = PRListResponse(
            stats=stats,
            pull_requests=pull_requests,
        )

        return response, pulls

    def get_pr_detail_data(
        self, pr_number: int
    ) -> Tuple[Dict[str, Any], GithubPullRequest]:
        pr = self.get_pr_details(pr_number)
        pr_data = self.format_pr_data(pr, include_comments=True)

        return {"pull_request": pr_data.dict()}, pr

    def get_prs_details_data(self, repo: str, days: int) -> Dict[str, Any]:
        pulls = self.search_merged_pull_requests(repo, days)

        pr_numbers = [pull.number for pull in pulls]
        pr_count = len(pr_numbers)

        pr_details = asyncio.run(self.get_pr_details_batch(pr_numbers))

        start_date, end_date = self.get_date_range(days)
        stats = Stats(
            repository=repo,
            days_analyzed=days,
            total_prs=pr_count,
            date_range=DateRange(
                start=self.format_date_ymd(start_date),
                end=self.format_date_ymd(end_date),
            ),
        )

        formatted_prs = [
            self.format_pr_data(pr, include_comments=True) for pr in pr_details
        ]

        return {
            "stats": stats.dict(),
            "pull_requests": [pr.dict() for pr in formatted_prs],
            "pr_details": pr_details,
        }
