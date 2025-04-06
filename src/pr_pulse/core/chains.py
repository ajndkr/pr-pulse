import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from rich.console import Console

from pr_pulse.constants import REPORT_PROMPT

from .fio import write_text_to_file

console = Console()


def generate_pr_summary_from_data(
    pr_data: dict[str, Any],
    llm: genai.Client,
    model: str = "gemini-2.0-flash",
    stream: bool = False,
    verbose: bool = False,
    write: bool = False,
) -> str:
    """Generates a PR Pulse insights summary using Gemini AI from PR data directly."""
    try:
        repository = pr_data["stats"]["repository"]
        days_analyzed = pr_data["stats"]["days_analyzed"]
    except KeyError as e:
        console.print(f"[bold red]error:[/] missing required key in PR data: {str(e)}")
        raise e

    if verbose:
        console.print("[bold blue]generating[/] summary...")

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="text/plain",
    )

    response = ""
    response_stream = llm.models.generate_content_stream(
        model=model,
        contents=REPORT_PROMPT.format(
            repository=repository,
            days_analyzed=days_analyzed,
            input_data=pr_data,
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


def generate_pr_summary_from_file(
    details_json_file: Path,
    llm: genai.Client,
    model: str = "gemini-2.0-flash",
    stream: bool = False,
    verbose: bool = False,
    write: bool = False,
) -> str:
    """Generates a PR Pulse insights summary using Gemini AI from a JSON file."""
    if verbose:
        console.print("[bold blue]reading[/] input file...")

    try:
        with open(details_json_file, "r") as f:
            input_data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]error:[/] failed to read input file: {str(e)}")
        raise e

    return generate_pr_summary_from_data(
        pr_data=input_data,
        llm=llm,
        model=model,
        stream=stream,
        verbose=verbose,
        write=write,
    )
