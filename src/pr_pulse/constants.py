from enum import Enum


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


MAX_COMMENTS = 5
BATCH_SIZE = 8
REPORT_PROMPT = """Generate an executive summary of the provided merged pull request activity. Pay attention at the pull request title, description and comments to understand the changes. Focus on top 5 functional changes and mention them in a bullet point list. For all other changes, mention them in a single paragraph of maximum 3 lines. Use Markdown formatting.

Data:

```json
{input_data}
```
"""
