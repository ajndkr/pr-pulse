from github import Auth, Github
from github.Repository import Repository
from google import genai
from rich.console import Console
from slack_sdk.webhook import WebhookClient

from pr_pulse.config import get_config

console = Console()


class ClientError(Exception):
    """Base exception for client errors"""

    pass


class AuthenticationError(ClientError):
    """Exception raised for authentication errors"""

    pass


class RepositoryError(ClientError):
    """Exception raised for repository access errors"""

    pass


class APIKeyError(ClientError):
    """Exception raised for API key errors"""

    pass


def setup_github_client(
    repo: str, verbose: bool = get_config().verbose
) -> tuple[Repository, Github]:
    """Sets up GitHub client and repository instance"""
    if not (github_token := get_config().github_token):
        console.print(
            "[bold red]error:[/] GitHub token not provided and not found in config"
        )
        raise AuthenticationError("GitHub token not provided")

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
        raise RepositoryError(f"Could not find repository {repo}: {str(e)}")


def setup_gemini_client(verbose: bool = get_config().verbose) -> genai.Client:
    """Sets up Gemini client"""
    if not (api_key := get_config().genai_api_key):
        console.print(
            "[bold red]error:[/] Gemini API key not provided and not found in config"
        )
        raise APIKeyError("Gemini API key not provided")

    if verbose:
        console.print("[bold blue]initializing[/] Gemini AI client...")

    return genai.Client(api_key=api_key)


def setup_slack_webhook_client(verbose: bool = get_config().verbose) -> WebhookClient:
    """Sets up Slack webhook client"""
    if not (webhook_url := get_config().slack_webhook_url):
        console.print(
            "[bold red]error:[/] Slack webhook URL not provided and not found in config"
        )
        raise APIKeyError("Slack webhook URL not provided")

    if verbose:
        console.print("[bold blue]initializing[/] Slack client...")

    return WebhookClient(webhook_url)
