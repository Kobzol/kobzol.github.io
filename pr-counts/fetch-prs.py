# /// script
# dependencies = ["github3api", "requests"]
# ///
import calendar
import dataclasses
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

import requests
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


def fetch_zulip_message_counts(zulip_id: int, months: list[Month]) -> dict:
    """Fetch counts of private (DM) and public (stream) messages sent by a user
    on the rust-lang.zulipchat.com Zulip server in the given months."""
    zulip_username = os.environ["ZULIP_USER"]
    zulip_token = os.environ["ZULIP_TOKEN"]
    months_set = set(months)
    min_month = months[0]
    max_month = months[-1]

    narrow = json.dumps([{"operator": "sender", "operand": zulip_id}])

    # Anchor the first page at the start of the target range (Zulip 12.0+), instead of
    # walking back from "newest" through every message posted after the target range.
    anchor_date = f"{min_month.year:04d}-{min_month.month:02d}-01T00:00:00Z"

    private_count = 0
    public_count = 0
    anchor = "date"
    num_after = 1000
    include_anchor = True
    page_num = 0

    print(f"Fetching Zulip messages for user id '{zulip_id}' in {months}...")

    while True:
        params = {
            "anchor": anchor,
            "anchor_date": anchor_date,
            "num_before": 0,
            "num_after": num_after,
            "narrow": narrow,
            "apply_markdown": "false",
            "include_anchor": "true" if include_anchor else "false",
        }

        response = requests.get(
            "https://rust-lang.zulipchat.com/api/v1/messages",
            auth=(zulip_username, zulip_token),
            params=params,
        )
        response.raise_for_status()
        result = response.json()
        messages = result["messages"]

        print(f"Page {page_num}, fetched {len(messages)} Zulip messages")
        page_num += 1

        stop = False
        for message in messages:
            assert message["sender_id"] == zulip_id
            sent_at = datetime.fromtimestamp(message["timestamp"], tz=timezone.utc)
            message_month = Month(sent_at.year, sent_at.month)
            if message_month in months_set:
                if message["type"] == "private":
                    private_count += 1
                else:
                    public_count += 1
            elif message_month > max_month:
                stop = True

        if stop or result.get("found_newest") or not messages:
            break

        anchor = messages[-1]["id"]
        include_anchor = False

    print(f"Total Zulip messages: {private_count} private, {public_count} public")
    return {"private_messages": private_count, "public_messages": public_count}


def fetch_github_comment_count_in_org(username: str, org: str, months: list[Month]) -> int:
    """Fetch the exact number of GitHub issue/PR comments made by a user in the given
    org during the given months, by searching for issues/PRs the user commented on and
    then counting their actual comments on each one."""
    token = os.environ["GITHUB_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    min_month = months[0]
    max_month = months[-1]
    from_date = f"{min_month.year:04d}-{min_month.month:02d}-01T00:00:00Z"
    last_day = calendar.monthrange(max_month.year, max_month.month)[1]
    to_date = f"{max_month.year:04d}-{max_month.month:02d}-{last_day:02d}T23:59:59Z"
    from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
    to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

    query = f"commenter:{username} org:{org}"

    print(f"Searching issues/PRs commented on by '{username}' in org '{org}'...")

    issues = []
    page = 1
    while True:
        response = requests.get(
            "https://api.github.com/search/issues",
            headers=headers,
            params={"q": query, "sort": "updated", "order": "desc", "per_page": 100, "page": page},
        )
        response.raise_for_status()
        items = response.json()["items"]

        stop = False
        for item in items:
            updated_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            if updated_at < from_dt:
                stop = True
                break
            issues.append(item)

        print(f"Search page {page}, fetched {len(items)} issues/PRs, total so far: {len(issues)}")
        if stop or len(items) < 100 or page >= 10:
            break
        page += 1

    print(f"Found {len(issues)} issues/PRs commented on by '{username}' in org '{org}'")

    total_comments = 0
    for i, issue in enumerate(issues):
        repo_full_name = issue["repository_url"].split("/repos/")[1]
        number = issue["number"]

        comments_page = 1
        while True:
            response = requests.get(
                f"https://api.github.com/repos/{repo_full_name}/issues/{number}/comments",
                headers=headers,
                params={"since": from_date, "per_page": 100, "page": comments_page},
            )
            response.raise_for_status()
            comments = response.json()

            for comment in comments:
                if comment["user"]["login"].lower() != username.lower():
                    continue
                created_at = datetime.fromisoformat(comment["created_at"].replace("Z", "+00:00"))
                if from_dt <= created_at <= to_dt:
                    total_comments += 1

            if len(comments) < 100:
                break
            comments_page += 1

        if (i + 1) % 25 == 0:
            print(f"Processed {i + 1}/{len(issues)} issues/PRs, comments so far: {total_comments}")

    print(f"Total comments by '{username}' in org '{org}': {total_comments}")
    return total_comments


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("github_username")
    parser.add_argument(
        "months",
        help='comma-separated list of "YYYY" or "YYYY-MM" values, e.g. "2026-06,2026-07" or "2026"',
    )
    parser.add_argument(
        "--zulip-id",
        type=int,
        default=None,
        help="Zulip user id; if set, also fetch message counts from rust-lang.zulipchat.com "
             "(requires ZULIP_USER and ZULIP_TOKEN env vars)",
    )
    args = parser.parse_args()

    username = args.github_username
    months = parse_months(args.months)
    label = label_for_months(args.months)

    gh = GitHubAPI(bearer_token=os.environ["GITHUB_TOKEN"])
    opened_prs = fetch_prs_opened_by_user(gh, username, months)
    reviewed_prs = fetch_prs_reviewed_by_user(gh, username, months)

    output = {"pull-requests": opened_prs, "reviews": reviewed_prs}

    if args.zulip_id is not None:
        output["zulip"] = fetch_zulip_message_counts(args.zulip_id, months)

    output["comment-count"] = fetch_github_comment_count_in_org(username, "rust-lang", months)

    with open(f"data-{label}.json", "w") as f:
        f.write(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()
