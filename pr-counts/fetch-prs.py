# /// script
# dependencies = ["github3api"]
# ///
import calendar
import dataclasses
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Literal

from github3api import GitHubAPI


@dataclasses.dataclass
class PullRequest:
    repo: str
    number: int
    title: str
    state: Literal["merged", "closed", "open"]
    created_at: str


@dataclasses.dataclass(frozen=True, order=True)
class Month:
    year: int
    month: int


def parse_months(months_arg: str) -> list[Month]:
    """
    Parse a comma-separated list of "YYYY" or "YYYY-MM" tokens into a sorted list
    of unique Month values. A bare year expands to all twelve months of that year.
    """
    months: set[Month] = set()
    for token in months_arg.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            year_str, month_str = token.split("-")
            months.add(Month(int(year_str), int(month_str)))
        else:
            year = int(token)
            for month in range(1, 13):
                months.add(Month(year, month))
    return sorted(months)


def label_for_months(months_arg: str) -> str:
    return months_arg.replace(",", "_")


def fetch_prs_opened_by_user(gh: GitHubAPI, username: str, months: list[Month]) -> dict:
    """Fetch all pull requests opened by a user in the given months."""
    months_set = set(months)
    min_month = months[0]

    # Define queries outside the loop
    query_first_page = """
query($login: String!) {
  user(login: $login) {
    pullRequests(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      nodes {
        createdAt
        number
        title
        url
        state
        repository {
          nameWithOwner
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

    query_with_cursor = """
query($login: String!, $cursor: String!) {
  user(login: $login) {
    pullRequests(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      nodes {
        createdAt
        number
        title
        url
        state
        repository {
          nameWithOwner
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

    prs_by_repo = defaultdict(list)
    print(f"Fetching PRs for user '{username}' opened in {months}...")

    total = 0
    cursor = None
    page_num = 0

    while True:
        # Use different queries depending on whether we have a cursor
        if cursor is None:
            variables = {"login": username}
            result = gh.graphql(query_first_page, variables)
        else:
            variables = {"login": username, "cursor": cursor}
            result = gh.graphql(query_with_cursor, variables)

        pr_data = result["data"]["user"]["pullRequests"]
        page_info = pr_data["pageInfo"]
        nodes = pr_data["nodes"]

        print(f"Page {page_num}, fetched {len(nodes)} PRs, total so far: {total}")
        page_num += 1

        stop = False
        for pr in nodes:
            created_at = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))

            # Check if PR was created in one of the target months
            pr_month = Month(created_at.year, created_at.month)
            if pr_month in months_set:
                pr_obj = PullRequest(
                    repo=pr["repository"]["nameWithOwner"],
                    number=pr["number"],
                    title=pr["title"],
                    state=pr["state"].lower(),
                    created_at=created_at.strftime("%d. %m.")
                )
                prs_by_repo[pr_obj.repo].append(dataclasses.asdict(pr_obj))
                total += 1
            elif pr_month < min_month:
                stop = True
                break

        if stop or not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    print(f"Total PRs: {total}")
    return prs_by_repo


def fetch_prs_reviewed_by_user(gh: GitHubAPI, username: str, months: list[Month]) -> dict:
    """Fetch all pull requests reviewed by a user in the given months."""
    months_set = set(months)
    min_month = months[0]
    max_month = months[-1]

    # Define date range spanning the earliest to the latest requested month
    from_date = f"{min_month.year:04d}-{min_month.month:02d}-01T00:00:00Z"
    last_day = calendar.monthrange(max_month.year, max_month.month)[1]
    to_date = f"{max_month.year:04d}-{max_month.month:02d}-{last_day:02d}T23:59:59Z"

    # GraphQL query for first page (without cursor)
    query_first_page = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      pullRequestReviewContributions(first: 100) {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          pullRequest {
            number
            title
            url
            state
            createdAt
            repository {
              nameWithOwner
            }
          }
          occurredAt
        }
      }
    }
  }
}
"""

    # GraphQL query for subsequent pages (with cursor)
    query_with_cursor = """
query($login: String!, $from: DateTime!, $to: DateTime!, $cursor: String!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      pullRequestReviewContributions(first: 100, after: $cursor) {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          pullRequest {
            number
            title
            url
            state
            createdAt
            repository {
              nameWithOwner
            }
          }
          occurredAt
        }
      }
    }
  }
}
"""

    prs_by_repo = defaultdict(list)
    print(f"Fetching PRs reviewed by user '{username}' in {months}...")

    total = 0
    cursor = None
    page_num = 0

    while True:
        # Use different queries depending on whether we have a cursor
        if cursor is None:
            variables = {
                "login": username,
                "from": from_date,
                "to": to_date
            }
            result = gh.graphql(query_first_page, variables)
        else:
            variables = {
                "login": username,
                "from": from_date,
                "to": to_date,
                "cursor": cursor
            }
            result = gh.graphql(query_with_cursor, variables)

        review_data = result["data"]["user"]["contributionsCollection"]["pullRequestReviewContributions"]
        page_info = review_data["pageInfo"]
        nodes = review_data["nodes"]

        print(f"Page {page_num}, fetched {len(nodes)} reviewed PRs, total so far: {total}")
        page_num += 1

        for review in nodes:
            pr = review["pullRequest"]
            created_at = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
            occurred_at = datetime.fromisoformat(review["occurredAt"].replace("Z", "+00:00"))

            # Only keep reviews that actually occurred in one of the target months
            if Month(occurred_at.year, occurred_at.month) not in months_set:
                continue

            pr_obj = PullRequest(
                repo=pr["repository"]["nameWithOwner"],
                number=pr["number"],
                title=pr["title"],
                state=pr["state"].lower(),
                created_at=created_at.strftime("%d. %m.")
            )
            prs_by_repo[pr_obj.repo].append(dataclasses.asdict(pr_obj))
            total += 1

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    print(f"Total reviewed PRs: {total}")
    return prs_by_repo


def main():
    if len(sys.argv) < 3:
        print("Usage: python fetch-prs.py <github_username> <months>")
        print('  <months> is a comma-separated list of "YYYY" or "YYYY-MM" values, e.g. "2026-06,2026-07" or "2026"')
        sys.exit(1)

    username = sys.argv[1]
    months = parse_months(sys.argv[2])
    label = label_for_months(sys.argv[2])

    gh = GitHubAPI(bearer_token=os.environ["GITHUB_TOKEN"])
    opened_prs = fetch_prs_opened_by_user(gh, username, months)
    reviewed_prs = fetch_prs_reviewed_by_user(gh, username, months)

    with open(f"prs-{label}.json", "w") as f:
        f.write(json.dumps({"pull-requests": opened_prs, "reviews": reviewed_prs}, indent=4))


if __name__ == "__main__":
    main()
