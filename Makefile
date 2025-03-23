.PHONY: help ci

help:	## help menu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init:	## initialize project
	uv sync
	uv run --only-dev pre-commit install

ci:		## run pre-commit checks
	uv run --only-dev pre-commit run --all

run:	## run project
	uv run pr-pulse

clean:	## clean project
	find . -type d -name '__pycache__' -exec rm -rfv {} +

clean-all: clean	## clean project and remove virtual environment
	rm -rf .venv
