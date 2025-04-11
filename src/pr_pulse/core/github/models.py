from typing import List, Optional

from pydantic import BaseModel


class DateRange(BaseModel):
    start: str
    end: str


class Stats(BaseModel):
    repository: str
    days_analyzed: int
    total_prs: int
    date_range: DateRange


class Comment(BaseModel):
    author: str
    created_at: str
    body: str


class PullRequest(BaseModel):
    number: int
    title: str
    author: str
    status: str
    created_at: str
    url: str
    description: str = ""
    merged_at: Optional[str] = None
    comments: Optional[List[Comment]] = None


class PRListResponse(BaseModel):
    stats: Stats
    pull_requests: List[PullRequest]


class PRDetailResponse(BaseModel):
    pull_request: PullRequest


class PRDetailsResponse(BaseModel):
    stats: Stats
    pull_requests: List[PullRequest]
