#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy the current localization-excel-updater skill into a target Git repo."
    )
    parser.add_argument("--skill-dir", required=True, help="Path to the source skill directory")
    parser.add_argument("--repo-dir", required=True, help="Path to the target local Git repository")
    parser.add_argument(
        "--target-folder",
        default="localization-excel-updater",
        help="Folder name to use inside the target repository",
    )
    parser.add_argument(
        "--doc",
        action="append",
        default=[],
        help="Optional extra file to copy into the repository root",
    )
    return parser.parse_args()


def ensure_directory(path: Path, label: str):
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {path}")


def ensure_file(path: Path, label: str):
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{label} is not a file: {path}")


def main():
    args = parse_args()
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    repo_dir = Path(args.repo_dir).expanduser().resolve()
    target_dir = repo_dir / args.target_folder

    ensure_directory(skill_dir, "Skill directory")
    ensure_directory(repo_dir, "Repository directory")
    if not (repo_dir / ".git").exists():
        raise FileNotFoundError(f"Target repository is not a Git repo: {repo_dir}")

    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(skill_dir, target_dir)

    copied_docs = []
    for doc in args.doc:
        source = Path(doc).expanduser().resolve()
        ensure_file(source, "Extra document")
        destination = repo_dir / source.name
        if source != destination:
            shutil.copy2(source, destination)
        copied_docs.append(str(destination))

    print("Published skill repository content:")
    print(f"- repo_dir: {repo_dir}")
    print(f"- target_dir: {target_dir}")
    if copied_docs:
        print("- copied_docs:")
        for item in copied_docs:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
