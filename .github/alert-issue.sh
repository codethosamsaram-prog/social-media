#!/usr/bin/env bash
# Tell the owner something broke by opening an issue assigned to them (GitHub emails it). Only one stays
# open per problem, because a run every 15 minutes would otherwise send an email every 15 minutes.
# It closes itself on recovery, so the next failure emails again. Needs GH_TOKEN and issues: write.
# Usage: alert-issue.sh "title" "body"   |   alert-issue.sh --clear "title"
set -euo pipefail

repo="$GITHUB_REPOSITORY"
find_open() {
  gh issue list --repo "$repo" --state open --limit 100 --json number,title \
    --jq "[.[] | select(.title == \"$1\")][0].number // empty"
}

if [ "$1" = "--clear" ]; then
  open=$(find_open "$2")
  if [ -n "$open" ]; then
    gh issue close "$open" --repo "$repo" --comment "Working again: $GITHUB_SERVER_URL/$repo/actions/runs/$GITHUB_RUN_ID"
  fi
  exit 0
fi

if [ -z "$(find_open "$1")" ]; then
  gh issue create --repo "$repo" --title "$1" --assignee "$GITHUB_REPOSITORY_OWNER" \
    --body "$2

Run: $GITHUB_SERVER_URL/$repo/actions/runs/$GITHUB_RUN_ID"
fi
