import argparse
import io
import json

IGNORED_ORGS = (
    "mcurlej", "Kobzol", "mrlvsb", "It4innovations", "geordi", "pyvec", "lerncz", "spirali",
    "nnethercote", "marco-test-org", "PyLadiesCZ", "messa", "traviscross", "andrewrk"
)
IGNORED_REPOS = (
    "bors-kindergarten",
    "bors-kindergarten2",
    "this-week-in-rust"
)

PR_LIST_MARKER = "<!-- pr-list -->"
PR_STATS_MARKER = "<!-- stats -->"


def is_valid_repo(repo: str) -> bool:
    (org, name) = repo.split("/")
    if org in IGNORED_ORGS:
        return False
    if name in IGNORED_REPOS:
        return False
    return True


def load_data(path: str) -> tuple[dict, dict, dict]:
    with open(path) as f:
        data = json.loads(f.read())
    return data["pull-requests"], data["reviews"], data["zulip"]


def render_pr_list(prs: dict) -> str:
    rust_prs = {k: v for (k, v) in prs.items() if is_valid_repo(k)}
    items = sorted(rust_prs.items(), key=lambda i: i[0])
    items = sorted(items, key=lambda i: len(i[1]), reverse=True)

    stream = io.StringIO()
    for (repo, repo_prs) in items:
        suffix = "s" if len(repo_prs) > 1 else ""
        print(f"### {repo} ({len(repo_prs)} PR{suffix})", file=stream)
        for pr in reversed(repo_prs):
            repo_full = pr["repo"]
            title = pr["title"]
            number = pr["number"]
            state = pr["state"]
            row = f"- [#{number}](https://github.com/{repo_full}/pull/{number}): {title}"
            if state == "closed":
                row += f' (<span style="color: red;">{state}</span>)'
            elif state == "open":
                row += f' (<span style="color: green;">{state}</span>)'
            elif state == "merged":
                row += f' (<span style="color: #8250DF;">{state}</span>)'
            print(row, file=stream)
        print(file=stream)
    return stream.getvalue()


def compute_stats(prs: dict, reviewed_prs: dict) -> tuple[int, int, int, int]:
    total_prs = sum(len(v) for v in prs.values())
    rust_prs = {k: v for (k, v) in prs.items() if is_valid_repo(k)}
    total_rust_prs = sum(len(v) for v in rust_prs.values())

    total_reviewed_prs = sum(len(v) for v in reviewed_prs.values())
    rust_reviewed_prs = {k: v for (k, v) in reviewed_prs.items() if is_valid_repo(k)}
    total_reviewed_rust_prs = sum(len(v) for v in rust_reviewed_prs.values())

    return total_prs, total_rust_prs, total_reviewed_prs, total_reviewed_rust_prs


def render_stats(prs: dict, reviewed_prs: dict, zulip_stats: dict, mode: str) -> str:
    total_prs, total_rust_prs, total_reviewed_prs, total_reviewed_rust_prs = compute_stats(prs, reviewed_prs)

    stream = io.StringIO()
    if mode == "rust-lang":
        print(f"- Opened **{total_rust_prs}** pull requests in Rust-related repositories.", file=stream)
        print(f"- Reviewed **{total_reviewed_rust_prs}** pull requests in Rust-related repositories.", file=stream)
    else:
        print(f"- Opened **{total_prs}** pull requests, of which **{total_rust_prs}** "
              f"({(total_rust_prs / total_prs) * 100:.2f}%) were in Rust-related repositories.", file=stream)
        print(f"- Reviewed **{total_reviewed_prs}** pull requests, of which **{total_reviewed_rust_prs}** "
              f"({(total_reviewed_rust_prs / total_reviewed_prs) * 100:.2f}%) were in Rust-related repositories.",
              file=stream)
    zulip_public_message = zulip_stats["public_messages"]
    zulip_private_message = zulip_stats["private_messages"]
    print(f"- Sent **{zulip_public_message}** public and **{zulip_private_message}** private messages on the [Rust Zulip](https://rust-lang.zulipchat.com).", file=stream)
    print(file=stream)
    return stream.getvalue()


def insert_after_marker(post: str, marker: str, content: str) -> str:
    """
    Insert `content` right after the line containing `marker`, replacing any
    previously generated content up to the next marker or `## ` heading.
    """
    post_modified = ""
    state = "copying"
    for line in post.splitlines(keepends=True):
        if state == "skipping" and (line.startswith("<!--") or line.startswith("## ")):
            state = "copying"

        if state == "copying":
            post_modified += line
            if line.startswith(marker):
                post_modified += "\n"
                post_modified += content
                state = "skipping"
        # lines in "skipping" state are dropped, since they hold stale generated content
    return post_modified


def render_post(prs: dict, reviewed_prs: dict, zulip_stats: dict, post_path: str, mode: str):
    with open(post_path) as f:
        post = f.read()

    post = insert_after_marker(post, PR_STATS_MARKER, render_stats(prs, reviewed_prs, zulip_stats, mode))
    post = insert_after_marker(post, PR_LIST_MARKER, render_pr_list(prs))

    with open(post_path, "w") as f:
        f.write(post)


def main():
    parser = argparse.ArgumentParser(description="Render fetched PR/review data into a blog post.")
    parser.add_argument("path", help="Path to the fetched data")
    parser.add_argument("post_path", help="Path to the blog post markdown file to render the data into")
    parser.add_argument("--mode", choices=["all", "rust-lang"], default="all",
                         help="If 'rust-lang', the PR stats only cover Rust-related repositories and omit the "
                              "total. If 'all', both the total and Rust-related counts are reported.")
    args = parser.parse_args()

    prs, reviewed_prs, zulip_stats = load_data(args.path)

    total_prs, total_rust_prs, total_reviewed_prs, total_reviewed_rust_prs = compute_stats(prs, reviewed_prs)
    print(f"Total PRs: {total_prs}, total Rust PRs: {total_rust_prs}, "
          f"{(total_rust_prs / total_prs) * 100:.2f}% is Rust Project")
    print(f"Total reviewed PRs: {total_reviewed_prs}, total reviewed Rust PRs: {total_reviewed_rust_prs}, "
          f"{(total_reviewed_rust_prs / total_reviewed_prs) * 100:.2f}% is Rust Project")

    render_post(prs, reviewed_prs, zulip_stats, args.post_path, args.mode)


if __name__ == "__main__":
    main()
