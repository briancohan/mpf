#!/usr/bin/env just --justfile

# Setup
install:
    @pipenv install

# Check formatting and syntax
check:
    @pipenv run pre-commit run --all-files

# Push to remote
push:
    @git push --set-upstream origin `git rev-parse --abbrev-ref HEAD`

# Dump requirements.txt
dump-req:
    pipenv requirements --exclude-markers > requirements.txt
    sed -i "s/\[.*\]//g" requirements.txt
