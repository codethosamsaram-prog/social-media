#!/usr/bin/env bash
# Tell the owner something broke: open an issue assigned to them (GitHub emails it), or add to the
# one already open so a bad day doesn't produce six separate issues. Needs GH_TOKEN and issues: write.
# Usage: alert-issue.sh "title" "body"
set -euo pipefail

repo="$GITHUB_REPOSITORY"
body="$2

Run: $GITHUB_SERVER_URL/$repo/actions/runs/$GITHUB_RUN_ID"

open=$(gh issue list --repo "$repo" --state open --limit 100 --json number,title \
  --jq "[.[] | select(.title == \"$1\")][0].number // empty")

if [ -n "$open" ]; then
  gh issue comment "$open" --repo "$repo" --body "$body"
else
  gh issue create --repo "$repo" --title "$1" --body "$body" --assignee "$GITHUB_REPOSITORY_OWNER"
fi
