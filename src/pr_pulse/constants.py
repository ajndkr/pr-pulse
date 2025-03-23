from enum import Enum


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


MAX_COMMENTS = 5
BATCH_SIZE = 8
REPORT_PROMPT = """Generate an executive summary of the provided merged pull request activity.

No headers are required in the summary. Mention the number of pull requests merged over the target period, mentioning only the elapsed days/weeks.

Pay attention to the pull request title, description and comments to understand the changes. Focus on top 5 functional changes and list them as bullet points, removing any conventional commit tags (like "feat:", "fix:", "chore:", "docs:", etc.) from the bullet points.

For all other changes, mention them in a single paragraph of maximum 3 lines.

Use Markdown formatting.

Data:

```json
{input_data}
```
"""
