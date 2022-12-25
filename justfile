#!/usr/bin/env just --justfile

# Setup
install:
    @pipenv install

# Development
test *args:
    @pipenv run pytest {{args}}

check:
    @pipenv run pre-commit run --all-files

# Publish
push:
    @git push --set-upstream origin `git rev-parse --abbrev-ref HEAD`
