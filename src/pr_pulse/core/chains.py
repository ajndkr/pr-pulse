import json
from pathlib import Path

from google import genai
from google.genai import types
from rich.console import Console

from pr_pulse.constants import REPORT_PROMPT

from .fio import write_text_to_file

console = Console()


def generate_pr_summary(
    details_json_file: Path,
    llm: genai.Client,
    model: str = "gemini-2.0-flash",
    stream: bool = False,
    verbose: bool = False,
    write: bool = False,
) -> str:
    """Generates a PR Pulse insights summary using Gemini AI."""
    if verbose:
        console.print("[bold blue]reading[/] input file...")

    try:
        with open(details_json_file, "r") as f:
            input_data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]error:[/] failed to read input file: {str(e)}")
        raise e

    try:
        repository = input_data["stats"]["repository"]
    except KeyError:
        console.print("[bold red]error:[/] missing 'repository' key in input file")
        raise e

    try:
        days_analyzed = input_data["stats"]["days_analyzed"]
    except KeyError:
        console.print("[bold red]error:[/] missing 'days_analyzed' key in input file")
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
            input_data=input_data,
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
