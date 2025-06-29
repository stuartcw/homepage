#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "alive_progress",
#   "dotenv",
#   "click"
# ]
# ///

from alive_progress import alive_bar
from datetime import datetime
from dotenv import load_dotenv
import click
import os
import platform
import re
import subprocess
import json
import sys


def open_file(file_path):
    """
    Open a file using the system's default application based on the operating system.

    This function abstracts away platform-specific details to allow a file
    (for example, a text file, PDF, image, etc.) to be opened using the
    system's default program. It supports Windows, macOS, and Linux.

    Parameters
    ----------
    file_path : str
        The full or relative path to the file that should be opened.

    Raises
    ------
    RuntimeError
        If the current operating system is not supported (i.e., not Windows,
        macOS, or Linux), a RuntimeError is raised with an explanatory message.

    Notes
    -----
    - On Windows, it uses `os.startfile()`.
    - On macOS, it uses the `open` command via `subprocess.run()`.
    - On Linux, it uses the `xdg-open` command via `subprocess.run()`.

    Example
    -------
    open_file("/path/to/report.pdf")
    """
    system = platform.system()
    if system == "Windows":
        os.startfile(file_path)
    elif system == "Darwin":  # macOS
        subprocess.run(["open", file_path])
    elif system == "Linux":
        subprocess.run(["xdg-open", file_path])
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")


def load_stop_dirs():
    """Load stop directories from .env file or use defaults."""
    env_stops = os.getenv("STOP_DIRS")
    default_stops = {
        "node_modules",
        ".git",
        "venv",
        "__pycache__",
        ".idea",
        ".vscode",
        "build",
        "dist",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".coverage",
        "htmlcov",
        ".env",
        ".venv",
        "env",
        ".DS_Store",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "*.so",
        "target",  # Rust/Cargo
        "vendor",  # Go dependencies
        "bin",
        "obj",  # .NET build directories
        "out",
        "logs",
        ".next",  # Next.js
        ".nuxt",  # Nuxt.js
    }

    if env_stops:
        # Combine with defaults, splitting the env string on commas
        return default_stops.union(set(env_stops.split(",")))
    return default_stops


def generate_anchor(rel_path):
    """Generate a Markdown anchor ID from a relative file path."""
    anchor = rel_path.lower().replace("_", "-")
    anchor = re.sub(r"[^a-z0-9-]", "-", anchor)
    anchor = re.sub(r"-+", "-", anchor)
    return anchor.strip("-")


def validate_doing_file(content, file_path):
    """Validate that .doing.md files start with ### heading."""
    if not content.strip().startswith("###"):
        return (
            file_path,
            f"Warning: {file_path} should start with a level-3 heading (###)",
        )
    if any(line.strip().startswith("##") for line in content.splitlines()):
        return file_path, f"Warning: {file_path} contains level-2 headings (##)"
    if any(
        line.strip().startswith("#") and not line.strip().startswith("###")
        for line in content.splitlines()
    ):
        return file_path, f"Warning: {file_path} contains level-1 headings (#)"
    return None


def get_doing_files_cache(root_dir):
    """Get the path to the doing files cache."""
    # We Cache doing_files to avoid re-reading. Check if recent doing_files.json exists.
    # Determine recent from a setting in the .env file. Otherewise, use 1 day.
    recent_days = os.getenv("RECENT_DAYS", 1)
    recent_days = int(recent_days)
    doing_files_cache = os.path.join(".", "doing_files.json")
    if os.path.exists(doing_files_cache):
        cache_mtime = os.path.getmtime(doing_files_cache)
        now = datetime.now().timestamp()
        if (now - cache_mtime) / (24 * 3600) < recent_days:
            with open(doing_files_cache, "r") as f:
                doing_files = json.load(f)
            return doing_files
    return None


def scan_doing_files(root_dir, stop_dirs, total_items):
    """Scan directory tree for .doing.md files and return list of file information."""
    doing_files = []
    errors = []

    with alive_bar(total_items, title="Scanning files") as bar:
        for current_dir, dirs, files in os.walk(root_dir):
            # Skip directories in the stop list
            dirs[:] = [d for d in dirs if d not in stop_dirs]

            for file in files:
                bar()  # Update progress bar
                if file == ".doing.md":
                    full_path = os.path.join(current_dir, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    try:
                        mtime = os.path.getmtime(full_path)
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if error_message := validate_doing_file(content, rel_path):
                                errors.append(error_message)

                            doing_files.append(
                                {
                                    "rel_path": rel_path,
                                    "mtime": mtime,
                                    "full_path": full_path,
                                    "content": content,
                                }
                            )
                    except (IOError, OSError) as e:
                        click.echo(f"Error reading {rel_path}: {str(e)}")
                        continue

    with open("errors.txt", "w") as error_file:
        for file_path, error in errors:
            error_file.write(f"{file_path}: {error}\n")
    # Save doing files to cache
    doing_files_cache = os.path.join(".", "doing_files.json")
    json.dump([file for file in doing_files], open(doing_files_cache, "w"))
    return doing_files, errors


@click.command()
@click.option(
    "--root-dir", default=str(os.path.expanduser("~")), help="Root directory to scan"
)
@click.option(
    "--ignore-cache",
    default=False,
    is_flag=True,
    help="Ignore cache and re-scan all files",
)
def main(root_dir, ignore_cache):
    """Generate a doing.md file aggregating all .doing.md files in a directory tree."""
    # Load environment variables from .env file
    load_dotenv()

    # Determine root directory from CLI or .env
    root_dir = root_dir or os.getenv("ROOT_DIR")
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        raise click.BadParameter(f"Directory not found: {root_dir}")

    # Load stop directories
    stop_dirs = load_stop_dirs()
    # Count total files for progress bar
    click.echo("Counting files...")
    total_items = sum([len(files) for _, _, files in os.walk(root_dir)])

    errors = []

    if not ignore_cache:
        doing_files = get_doing_files_cache("root_dir")

    if not doing_files:
        doing_files, errors = scan_doing_files(root_dir, stop_dirs, total_items)

    # Sort files by modification time (newest first)
    doing_files.sort(key=lambda x: x["mtime"], reverse=True)

    # Generate Markdown content
    with alive_bar(len(doing_files), title="Generating output") as bar:
        index = [
            "# Index of .doing.md Files\n",
            "Sorted by last modified time (newest first):\n",
        ]
        content = ["\n# Aggregated Content\n"]

        for file in doing_files:
            # Generate index entry
            timestamp = datetime.fromtimestamp(file["mtime"]).strftime("%Y-%m-%d %H:%M")
            anchor = generate_anchor(file["rel_path"])
            index.append(f"- [{timestamp}] [{file['rel_path']}](#{anchor})")

            # Generate content section
            content.extend(
                [
                    f'<a id="{anchor}"></a>',
                    f'## {file["rel_path"]}\n',
                    f"**Last modified**: {timestamp}\n",
                    f"{file['content']}\n",
                    "---\n",
                ]
            )
            bar()  # Update progress bar

        if errors:
            content.append("\n# Warnings\n")
            for file_path, error in errors:
                content.append(f"- {error}\n")

            # Add a footer
        content.append("\n---\n")
        content.append(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by dot_doing.py\n"
        )

        # Combine all parts and write to file
        output_path = os.path.join(root_dir, "doing.md")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(index + content))
            click.echo(f"Successfully generated: {output_path}")
            open_file(output_path)

        except IOError as e:
            click.echo(f"Error writing output file: {str(e)}")


if __name__ == "__main__":
    main()
