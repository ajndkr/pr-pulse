from enum import Enum


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


MAX_COMMENTS = 5
BATCH_SIZE = 8
REPORT_PROMPT = """Generate an executive summary of the pull request activity for the `{repository}` repository over the past {days_analyzed} days.

Start with a brief overview stating the total number of merged PRs and end with a 👏 emoji.

Next, provide 3-5 detailed bullet points highlighting the most significant changes based on:
- Impact on user experience or functionality
- Architectural changes or major refactoring
- New features or capability additions
- Security improvements
- Performance optimizations

For each significant change:
- Extract the core purpose (ignoring conventional commit prefixes)
- Examine PR discussions for implementation details or challenges
- Note any dependencies or related work

Conclude with a brief paragraph summarizing other notable changes and end with a 🙌 emoji.

Use professional, technical language with Markdown formatting.

Data:

```json
{input_data}
```
"""
