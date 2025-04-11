import json
from pathlib import Path
from typing import Any, Dict

from google import genai
from google.genai import types
from rich.console import Console

from pr_pulse.constants import REPORT_PROMPT
from pr_pulse.models import Stats

from .io import write_text_to_file

console = Console()


class SummaryGenerationError(Exception):
    """Exception raised for errors during summary generation"""

    pass


def generate_pr_summary_from_data(
    pr_data: Dict[str, Any],
    llm: genai.Client,
    model: str = "gemini-2.0-flash",
    stream: bool = False,
    verbose: bool = False,
    write: bool = False,
) -> str:
    """Generates a PR Pulse insights summary using Gemini AI from PR data directly"""
    try:
        # Try to parse stats as a Pydantic model if it's a dict
        if isinstance(pr_data["stats"], dict):
            stats = Stats(**pr_data["stats"])
            repository = stats.repository
            days_analyzed = stats.days_analyzed
        else:
            # If it's already a Pydantic model
            repository = pr_data["stats"].repository
            days_analyzed = pr_data["stats"].days_analyzed
    except KeyError as e:
        error_msg = f"Missing required key in PR data: {str(e)}"
        console.print(f"[bold red]error:[/] {error_msg}")
        raise SummaryGenerationError(error_msg)
    except Exception as e:
        error_msg = f"Failed to parse PR data: {str(e)}"
        console.print(f"[bold red]error:[/] {error_msg}")
        raise SummaryGenerationError(error_msg)

    if verbose:
        console.print("[bold blue]generating[/] summary...")

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="text/plain",
    )

    try:
        # Convert Pydantic models to dict for serialization
        serializable_data = {}
        for key, value in pr_data.items():
            if hasattr(value, "dict") and callable(getattr(value, "dict")):
                serializable_data[key] = value.dict()
            elif isinstance(value, list) and all(
                hasattr(item, "dict") and callable(getattr(item, "dict"))
                for item in value
            ):
                serializable_data[key] = [item.dict() for item in value]
            else:
                serializable_data[key] = value

        response = ""
        response_stream = llm.models.generate_content_stream(
            model=model,
            contents=REPORT_PROMPT.format(
                repository=repository,
                days_analyzed=days_analyzed,
                input_data=serializable_data,
            ),
            config=generate_content_config,
        )

        for chunk in response_stream:
            if stream:
                console.print(chunk.text, end="")
            response += chunk.text

        if not stream:
            console.print(response)

        if write:
            if verbose:
                console.print("[bold blue]writing[/] report to file...")
            write_text_to_file(response, "pr-pulse-report", verbose)

        return response
    except Exception as e:
        error_msg = f"Failed to generate summary: {str(e)}"
        console.print(f"[bold red]error:[/] {error_msg}")
        raise SummaryGenerationError(error_msg)


def generate_pr_summary_from_file(
    details_json_file: Path,
    llm: genai.Client,
    model: str = "gemini-2.0-flash",
    stream: bool = False,
    verbose: bool = False,
    write: bool = False,
) -> str:
    """Generates a PR Pulse insights summary using Gemini AI from a JSON file"""
    if verbose:
        console.print("[bold blue]reading[/] input file...")

    try:
        with open(details_json_file, "r") as f:
            input_data = json.load(f)
    except Exception as e:
        error_msg = f"Failed to read input file: {str(e)}"
        console.print(f"[bold red]error:[/] {error_msg}")
        raise SummaryGenerationError(error_msg)

    return generate_pr_summary_from_data(
        pr_data=input_data,
        llm=llm,
        model=model,
        stream=stream,
        verbose=verbose,
        write=write,
    )
