from enum import Enum


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


MAX_COMMENTS = 5
BATCH_SIZE = 8
REPORT_PROMPT = """Generate a structured report of the provided pull request activity in JSON format.

Use this JSON schema:

Report = {'summary': str, 'details': list[str]}
Return: Report.

'summary': contains an executive summary of all changes. mention the number of pull requests merged and top 5 changes across all pull requests as bullet point list. use markdown format.
'details': contains functional requirement document of all changes. keep it single paragraph and maximum of 3 sentences. refer to pull request url for more details. use markdown format.

Data:

```json
{input_data}
```
"""
