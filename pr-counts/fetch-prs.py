# /// script
# dependencies = ["github3api"]
# ///
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


def fetch_prs_opened_by_user(gh: GitHubAPI, username: str, year=2025):
    """Fetch all pull requests opened by a user in a specific year."""
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
    print(f"Fetching PRs for user '{username}' opened in {year}...")

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

            # Check if PR was created in the target year
            if created_at.year == year:
                pr_obj = PullRequest(
                    repo=pr["repository"]["nameWithOwner"],
                    number=pr["number"],
                    title=pr["title"],
                    state=pr["state"].lower(),
                    created_at=created_at.strftime("%d. %m.")
                )
                prs_by_repo[pr_obj.repo].append(dataclasses.asdict(pr_obj))
                total += 1
            elif created_at.year < year:
                stop = True
                break

        if stop or not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    print(f"Total PRs: {total}")
    with open(f"prs-{year}.json", "w") as f:
        f.write(json.dumps(prs_by_repo, indent=4))


def fetch_prs_reviewed_by_user(gh: GitHubAPI, username: str, year=2025):
    """Fetch all pull requests reviewed by a user in a specific year."""
    # Define date range for the year
    from_date = f"{year}-01-01T00:00:00Z"
    to_date = f"{year}-12-31T23:59:59Z"

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
    print(f"Fetching PRs reviewed by user '{username}' in {year}...")

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
    with open(f"reviews-{year}.json", "w") as f:
        f.write(json.dumps(prs_by_repo, indent=4))


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch-prs.py <github_username> [year]")
        sys.exit(1)

    username = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

    gh = GitHubAPI(bearer_token=os.environ["GITHUB_TOKEN"])
    fetch_prs_opened_by_user(gh, username, year)
    fetch_prs_reviewed_by_user(gh, username, year)


if __name__ == "__main__":
    main()
