import subprocess
from pathlib import Path
from typing import Any

from agno.tools import tool


@tool(description="Get the current git status of the repository")
def git_status() -> str:
    """Get git status in short format."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    output = result.stdout.strip()
    if not output:
        return "Working tree clean"
    return output


@tool(description="Get the git diff of changed files")
def git_diff() -> str:
    """Get git diff of staged and unstaged changes."""
    result = subprocess.run(
        ["git", "diff", "--no-color"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip() or "No changes"


@tool(description="Get staged changes in git")
def git_diff_cached() -> str:
    """Get git diff of staged changes."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--no-color"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip() or "No staged changes"


@tool(description="Create a git commit with the given message")
def git_commit(message: str) -> str:
    """Create a git commit with the provided message."""
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return f"Committed: {message}"


@tool(description="Push commits to remote repository")
def git_push() -> str:
    """Push commits to remote."""
    result = subprocess.run(
        ["git", "push"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return "Pushed to remote"


@tool(description="Get recent git commit history")
def git_log(limit: int = 5) -> str:
    """Get recent git commits."""
    result = subprocess.run(
        ["git", "log", f"-{limit}", "--oneline", "--no-color"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return result.stdout.strip() or "No commits"


@tool(description="Show file contents without editing")
def preview_file(file_path: str, lines: int = 50) -> str:
    """Preview contents of a file."""
    path = Path(file_path).expanduser()
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.is_file():
        return f"Error: Not a file: {file_path}"
    try:
        with open(path) as f:
            content = f.read()
        if len(content.splitlines()) > lines:
            return (
                "\n".join(content.splitlines()[:lines])
                + f"\n... ({len(content.splitlines()) - lines} more lines)"
            )
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@tool(description="List files in a directory")
def list_directory(path: str = ".") -> str:
    """List files in a directory."""
    dir_path = Path(path).expanduser()
    if not dir_path.exists():
        return f"Error: Directory not found: {path}"
    if not dir_path.is_dir():
        return f"Error: Not a directory: {path}"
    try:
        entries = []
        for entry in dir_path.iterdir():
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        return "\n".join(sorted(entries)) or "(empty)"
    except Exception as e:
        return f"Error listing directory: {e}"


def get_default_tools() -> list[Any]:
    return [
        git_status,
        git_diff,
        git_diff_cached,
        git_commit,
        git_push,
        git_log,
        preview_file,
        list_directory,
    ]
