#!/usr/bin/env bash
# Instructions to remove `.env` from git history using BFG or git-filter-repo.
# Run locally; this will rewrite history and requires a force-push.

set -euo pipefail

echo "This script shows recommended commands — review before running."

echo "Option A: Using the BFG Repo-Cleaner"
echo "1) Download BFG: https://rtyley.github.io/bfg-repo-cleaner/"
echo "2) Mirror your repo locally:"
echo "   git clone --mirror git@github.com:your/repo.git"
echo "   cd repo.git"
echo "3) Run BFG to delete .env files:"
echo "   java -jar bfg.jar --delete-files .env"
echo "4) Cleanup:"
echo "   git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "5) Push rewritten history (force): git push --force"

echo "Option B: Using git-filter-repo (recommended)"
echo "1) Install git-filter-repo (pip install git-filter-repo or package manager)"
echo "2) From your repo root run:"
echo "   git filter-repo --invert-paths --path .env --force"
echo "3) Force-push the cleaned repo: git push --force"

echo "After cleaning: rotate all keys and revoke compromised credentials immediately."
