# pr-pulse

Analyze merged pull requests and generate insights.

## usage

#### basic example

```yaml
name: pr-pulse-insights
on:
  schedule:
    - cron: "0 8 * * 1" # Runs at 8:00 AM UTC every Monday

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: generate insights summary
        uses: ajndkr/pr-pulse@v0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          repository: "owner/repo"
          days: "7"
```

#### input parameters

| Parameter           | Description                            | Required | Default |
| ------------------- | -------------------------------------- | -------- | ------- |
| `github_token`      | GitHub token for repository access     | Yes      | -       |
| `api_key`           | GEMINI API key for `report` command    | No       | -       |
| `slack_webhook_url` | Slack webhook URL for `share` command  | No       | -       |
| `command`           | Command to run (summary, share)        | No       | summary |
| `repository`        | Target repository in format owner/repo | Yes      | -       |
| `days`              | Number of days to look back for PRs    | No       | 7       |

**Note:** To create a Slack webhook URL, refer to
[Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks).

## local development

### pre-requisites

- [uv](https://docs.astral.sh/uv/#getting-started)

### init project

```shell
make init
```

to run pre-commit checks, run:

```shell
make ci
```

### run commands

run the following to view the list of available commands:

```shell
make run
```

## project roadmap

### phase 1

- [x] setup project
- [x] create commands to fetch data from github
- [x] convert project to github action to schedule cron jobs in target
      repository
- [x] add llm integration to generate weekly report
- [x] add slack integration to send weekly report

### phase 2

- [ ] improve customisability of commands
- [ ] add MCP support
- [ ] add support for more LLM providers
