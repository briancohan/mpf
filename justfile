#!/usr/bin/env just --justfile

# Show this help
list:
    just --list


# Setup
install:
    @pipenv install


# Check formatting and syntax
check:
    @pipenv run pre-commit run --all-files


# Format code with Ruff
format:
    @ruff check --select I --fix
    @ruff format


# Lint code with Ruff
lint:
    @ruff check --fix


# Run mypy
mypy:
    @pipenv run mypy .


# Push to remote
push:
    @git push --set-upstream origin `git rev-parse --abbrev-ref HEAD`
