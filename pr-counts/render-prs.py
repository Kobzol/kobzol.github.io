import io
import json
import sys


def is_valid_repo(repo: str) -> bool:
    (org, name) = repo.split("/")
    if org in ("mcurlej", "Kobzol", "mrlvsb", "It4innovations", "geordi", "pyvec", "lerncz", "spirali", "nnethercote", "marco-test-org", "PyLadiesCZ", "messa"):
        return False
    if "bors-kindergarten" in name:
        return False
    return True


year = sys.argv[1]
with open(f"prs-{year}.json") as f:
    prs = json.loads(f.read())

with open(f"reviews-{year}.json") as f:
    reviewed_prs = json.loads(f.read())

total_reviewed_prs = sum(len(v) for v in reviewed_prs.values())
rust_reviewed_prs = {k: v for (k, v) in reviewed_prs.items() if is_valid_repo(k)}
total_reviewed_rust_prs = sum(len(v) for v in rust_reviewed_prs.values())
print(f"Total reviewed PRs: {total_reviewed_prs}, total reviewed Rust PRs: {total_reviewed_rust_prs}, {(total_reviewed_rust_prs / total_reviewed_prs) * 100:.2f}% is Rust Project")

total_prs = sum(len(v) for v in prs.values())

rust_prs = {k: v for (k, v) in prs.items() if is_valid_repo(k)}
total_rust_prs = sum(len(v) for v in rust_prs.values())

print(f"Total PRs: {total_prs}, total Rust PRs: {total_rust_prs}, {(total_rust_prs / total_prs) * 100:.2f}% is Rust Project")

items = sorted(rust_prs.items(), key=lambda i: i[0])
items = sorted(items, key=lambda i: len(i[1]), reverse=True)

print(f"Total Rust repo count: {len(items)}")

stream = io.StringIO()
for (repo, prs) in items:
    suffix = "s" if len(prs) > 1 else ""
    print(f"### {repo} ({len(prs)} PR{suffix})", file=stream)
    for pr in reversed(prs):
        repo = pr["repo"]
        title = pr["title"]
        number = pr["number"]
        created_at = pr["created_at"]
        state = pr["state"]
        row = f"- [#{number}](https://github.com/{repo}/pull/{number}): {title}"
        if state == "closed":
            row += f' (<span style="color: red;">{state}</span>)'
        elif state == "open":
            row += f' (<span style="color: green;">{state}</span>)'
        print(row, file=stream)
    print(file=stream)

post_path = sys.argv[2]
with open(post_path) as f:
    post = f.read()

post_modified = ""
state = "copying"
for line in post.splitlines(keepends=True):
    if line.startswith("title:"):
        post_modified += f'title: "{total_rust_prs} PRs to improve Rust in 2025"\n'
        continue

    if state == "skipping" and line.startswith("## "):
        state = "copying"

    if state == "copying":
        post_modified += line
        if line.startswith("<!-- pr-list -->"):
            post_modified += "\n"
            post_modified += stream.getvalue()
            state = "skipping"


with open(post_path, "w") as f:
    f.write(post_modified)
