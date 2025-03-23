# pr-pulse

generate weekly reports of all code changes in a github repository.

## usage

run the following to view the list of available commands.

```shell
make run
```

## getting started

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
- [ ] add llm integration to generate weekly report
- [ ] add slack integration to send weekly report
- [ ] convert project to GitHub action to schedule cron jobs in target repository
