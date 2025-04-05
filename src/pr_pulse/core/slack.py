import re


def create_report_text(report: str) -> str:
    """Creates Slack-compatible formatted text from a markdown report.

    Transforms standard markdown to Slack's markdown variant by:
    - Converting headers (##) and bold text (**) to Slack's bold syntax (*)
    - Ensuring proper spacing around lists for Slack rendering
    - Formatting code blocks with proper spacing
    - Converting HTML code tags to backticks
    - Reformatting links from [text](url) to Slack's <url|text> format
    """
    processed_report = report

    # convert standard markdown headings/bold to Slack format
    processed_report = re.sub(r"##\s+(.+)", r"*\1*", processed_report)
    processed_report = re.sub(r"\*\*(.*?)\*\*", r"*\1*", processed_report)

    # add necessary spacing before list items for Slack rendering
    processed_report = re.sub(
        r"([^\n])\n([\*\-\d+]\.?\s)", r"\1\n\n\2", processed_report
    )

    # ensure code blocks have proper Slack-required spacing
    processed_report = re.sub(r"```([^`]+)```", r"```\n\1\n```", processed_report)

    # convert HTML code tags to markdown backticks
    processed_report = re.sub(r"<code>(.*?)</code>", r"`\1`", processed_report)

    # convert markdown links to Slack's link format
    processed_report = re.sub(r"\[(.*?)\]\((.*?)\)", r"<\2|\1>", processed_report)

    return f"*PR Pulse Report*\n\n{processed_report}"
