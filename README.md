# pr-weekly

generate weekly reports of all code changes in a github repository.

## usage

### local usage

run the following to view the list of available commands:

```shell
make run
```

### github action usage

pr-pulse can be used as a github action to automatically generate reports on a
schedule.

#### basic example

```yaml
name: weekly-pr-report
on:
  schedule:
    - cron: "0 8 * * 1" # Runs at 8:00 AM UTC every Monday

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - name: generate pr report
        uses: ajndkr/pr-pulse@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          repository: "owner/repo"
          days: "7"
          command: "summary"
```

#### input parameters

| Parameter       | Description                                            | Required | Default |
| --------------- | ------------------------------------------------------ | -------- | ------- |
| `github_token`  | GitHub token for repository access                     | Yes      | -       |
| `repository`    | Target repository in format owner/repo                 | Yes      | -       |
| `days`          | Number of days to look back for PRs                    | No       | 7       |
| `output_format` | Output format (table or json)                          | No       | table   |
| `verbose`       | Show detailed progress logs                            | No       | false   |
| `command`       | Command to run (list, detail, summary)                 | No       | summary |
| `pr_number`     | Pull request number (required only for detail command) | No       | -       |

## getting started (local development)

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

## project roadmap

- [x] setup project
- [x] create commands to fetch data from github
- [x] convert project to github action to schedule cron jobs in target
      repository
- [ ] add llm integration to generate weekly report
- [ ] add slack integration to send weekly report
