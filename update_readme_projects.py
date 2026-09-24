"""
Fetches all public, non-fork repos for a GitHub user and writes them as a
Markdown table into README.md, between the PROJECTS-LIST markers.
Run by the GitHub Action on a schedule / on push.
"""

import os
import re
import requests

USERNAME = "hanzlabaig-dev"
README_PATH = "README.md"
START_MARKER = "<!-- PROJECTS-LIST:START -->"
END_MARKER = "<!-- PROJECTS-LIST:END -->"

# Optional: skip these repo names (e.g. your own profile README repo)
EXCLUDE = {USERNAME, f"{USERNAME}.github.io"}


def fetch_repos():
    repos = []
    page = 1
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&sort=updated"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1

    # Filter out forks and excluded repos
    repos = [r for r in repos if not r["fork"] and r["name"] not in EXCLUDE]
    return repos


def build_table(repos):
    lines = [
        "| Project | Description | Language | Stars |",
        "|---|---|---|---|",
    ]
    for r in repos:
        name = r["name"]
        url = r["html_url"]
        desc = (r["description"] or "No description yet").replace("|", "-")
        lang = r["language"] or "-"
        stars = r["stargazers_count"]
        lines.append(f"| [{name}]({url}) | {desc} | {lang} | ⭐ {stars} |")
    return "\n".join(lines)


def update_readme(table_md):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{table_md}\n{END_MARKER}"

    if pattern.search(content):
        content = pattern.sub(replacement, content)
    else:
        content += f"\n\n{replacement}\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    repos = fetch_repos()
    table = build_table(repos)
    update_readme(table)
    print(f"Updated README with {len(repos)} repos.")
