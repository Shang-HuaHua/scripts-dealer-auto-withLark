#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run_git(args, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def normalize_remote_url(remote_url: str) -> str:
    remote_url = remote_url.strip()
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]

    if remote_url.startswith("git@"):
        host_and_path = remote_url[4:]
        if ":" not in host_and_path:
            raise ValueError(f"Unsupported Git remote format: {remote_url}")
        host, path = host_and_path.split(":", 1)
        return f"http://{host}/{path}"

    if remote_url.startswith("ssh://git@"):
        host_and_path = remote_url[len("ssh://git@") :]
        parts = host_and_path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Unsupported Git remote format: {remote_url}")
        host = parts[0]
        path = parts[1]
        if ":" in host:
            host = host.split(":", 1)[0]
        return f"http://{host}/{path}"

    if remote_url.startswith("http://") or remote_url.startswith("https://"):
        return remote_url

    raise ValueError(f"Unsupported Git remote format: {remote_url}")


def build_links(workspace: Path) -> dict:
    commit_sha = run_git(["rev-parse", "HEAD"], workspace)
    short_sha = run_git(["rev-parse", "--short", "HEAD"], workspace)
    remote_url = run_git(["remote", "get-url", "origin"], workspace)
    repository_url = normalize_remote_url(remote_url)
    commit_url = f"{repository_url}/-/commit/{commit_sha}"
    return {
        "workspace": str(workspace),
        "remote_url": remote_url,
        "repository_url": repository_url,
        "commit_sha": commit_sha,
        "short_sha": short_sha,
        "commit_url": commit_url,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build clickable GitLab repository and commit links for the current repo."
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Git repository root or any path inside the repository. Defaults to the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    links = build_links(workspace)

    if args.json:
        print(json.dumps(links, ensure_ascii=False, indent=2))
        return

    print(f"仓库: {links['repository_url']}")
    print(f"本次提交: {links['commit_url']}")


if __name__ == "__main__":
    main()
