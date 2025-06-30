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
import sqlite3
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
        # Temporary/junk directories
        "junk",  # General junk/temporary files directory
        
        # Version control and development environments
        ".git",  # Git repository metadata - no user content
        ".rbenv",  # Ruby version manager - system files only
        ".pyenv",  # Python version manager - system files only
        ".nvm",  # Node Version Manager - system files only
        ".rustup",  # Rust toolchain manager - system files only
        
        # System directories
        "Library",  # macOS system library - system files only
        ".DS_Store",  # macOS directory metadata - system files only
        ".cache",  # General cache directory - temporary files
        "Downloads",  # User downloads folder - typically not project content
        ".Trash",  # System trash folder - deleted files
        "Bundles",  # macOS application bundles - system files only
        ".meteor",  # Meteor framework cache - can be regenerated
        
        # Package managers and dependencies
        "node_modules",  # Node.js dependencies - can be regenerated
        "vendor",  # Go/PHP/Ruby dependencies - can be regenerated
        "site-packages",  # Python packages - installed via pip
        
        # Python virtual environments and cache
        "venv",  # Python virtual environment - can be recreated
        ".venv",  # Python virtual environment - can be recreated
        "env",  # Python virtual environment - can be recreated
        ".env",  # Environment variables file - may contain secrets
        "__pycache__",  # Python bytecode cache - can be regenerated
        "*.pyc",  # Python compiled bytecode - can be regenerated
        "*.pyo",  # Python optimized bytecode - can be regenerated
        "*.pyd",  # Python extension modules - can be regenerated
        ".Python",  # Python symlink in venv - part of venv
        "*.so",  # Shared object files - compiled binaries
        
        # IDE and editor directories
        ".idea",  # IntelliJ/PyCharm project files - IDE-specific
        ".vscode",  # VS Code settings - IDE-specific
        ".vim",  # Vim configuration - editor-specific
        ".cursor",  # Cursor AI editor files - IDE-specific
        
        # Build and output directories
        "build",  # Build output directory - can be regenerated
        "dist",  # Distribution/build output - can be regenerated
        "out",  # General output directory - can be regenerated
        "obj",  # .NET build objects - can be regenerated
        "bin",  # Binary/executable output - can be regenerated
        "target",  # Rust/Cargo build output - can be regenerated
        
        # Testing and coverage directories
        ".pytest_cache",  # Pytest cache - can be regenerated
        ".mypy_cache",  # MyPy type checker cache - can be regenerated
        ".tox",  # Tox testing environments - can be regenerated
        ".coverage",  # Coverage.py data - can be regenerated
        "htmlcov",  # Coverage HTML reports - can be regenerated
        
        # Log files
        "logs",  # Log files directory - typically not user content
        
        # Framework-specific directories
        ".next",  # Next.js build cache - can be regenerated
        ".nuxt",  # Nuxt.js build cache - can be regenerated
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


def init_sqlite_cache():
    """Initialize SQLite cache database."""
    cache_path = os.path.expanduser("~/.doing.cache.sqlite")
    conn = sqlite3.connect(cache_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS folder_cache (
            folder_path TEXT PRIMARY KEY,
            has_doing_md BOOLEAN,
            subfolders_ignored BOOLEAN,
            depth INTEGER,
            last_checked TIMESTAMP,
            mtime REAL,
            content TEXT
        )
    """)
    conn.commit()
    return conn

def get_cached_folders(root_dir):
    """Get cached folder information that's still fresh (within 1 day)."""
    conn = init_sqlite_cache()
    cutoff_time = datetime.now().timestamp() - (24 * 3600)  # 1 day ago
    
    cursor = conn.execute("""
        SELECT folder_path, has_doing_md, mtime, content 
        FROM folder_cache 
        WHERE last_checked > ? AND has_doing_md = 1
    """, (cutoff_time,))
    
    cached_doing_files = []
    for row in cursor.fetchall():
        folder_path, has_doing_md, mtime, content = row
        if has_doing_md:
            cached_doing_files.append({
                "rel_path": os.path.relpath(folder_path, root_dir),
                "mtime": mtime,
                "full_path": os.path.join(folder_path, ".doing.md"),
                "content": content
            })
    
    conn.close()
    return cached_doing_files


def scan_doing_files(root_dir, stop_dirs):
    """Scan directory tree for .doing.md files and return list of file information."""
    doing_files = []
    errors = []
    conn = init_sqlite_cache()
    cutoff_time = datetime.now().timestamp() - (24 * 3600)  # 1 day ago
    current_time = datetime.now().timestamp()

    # Count directories for progress bar
    click.echo("Building cache and scanning for .doing.md files...")
    total_dirs = sum(1 for _ in os.walk(root_dir))
    
    with alive_bar(total_dirs, title="Scanning directories") as bar:
        for current_dir, dirs, files in os.walk(root_dir):
            # Calculate depth relative to root_dir
            depth = current_dir.replace(root_dir, '').count(os.sep)
            
            # Check if this folder was recently checked
            cursor = conn.execute("""
                SELECT has_doing_md, mtime, content, last_checked 
                FROM folder_cache 
                WHERE folder_path = ?
            """, (current_dir,))
            
            cached_row = cursor.fetchone()
            
            # Skip directories in the stop list
            original_dirs = dirs[:]
            dirs[:] = [d for d in dirs if d not in stop_dirs]
            subfolders_ignored = len(original_dirs) != len(dirs)
            
            bar()  # Update progress bar for each directory
            
            has_doing_md = ".doing.md" in files
            
            # If we have fresh cache data, use it
            if cached_row and cached_row[3] > cutoff_time:
                cached_has_doing, cached_mtime, cached_content, _ = cached_row
                if cached_has_doing and has_doing_md:
                    dir_rel_path = os.path.relpath(current_dir, root_dir)
                    doing_files.append({
                        "rel_path": dir_rel_path,
                        "mtime": cached_mtime,
                        "full_path": os.path.join(current_dir, ".doing.md"),
                        "content": cached_content,
                    })
                continue
            
            # Process new/stale data
            content = ""
            mtime = None
            
            if has_doing_md:
                full_path = os.path.join(current_dir, ".doing.md")
                dir_rel_path = os.path.relpath(current_dir, root_dir)
                try:
                    mtime = os.path.getmtime(full_path)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if error_message := validate_doing_file(content, dir_rel_path):
                            errors.append(error_message)
                        
                        doing_files.append({
                            "rel_path": dir_rel_path,
                            "mtime": mtime,
                            "full_path": full_path,
                            "content": content,
                        })
                except (IOError, OSError) as e:
                    click.echo(f"Error reading {dir_rel_path}/.doing.md: {str(e)}")
                    has_doing_md = False
            
            # Update cache
            conn.execute("""
                INSERT OR REPLACE INTO folder_cache 
                (folder_path, has_doing_md, subfolders_ignored, depth, last_checked, mtime, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (current_dir, has_doing_md, subfolders_ignored, depth, current_time, mtime, content))

    conn.commit()
    conn.close()

    with open("errors.txt", "w") as error_file:
        for file_path, error in errors:
            error_file.write(f"{file_path}: {error}\n")
    
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
    errors = []
    doing_files = []

    if not ignore_cache:
        doing_files = get_cached_folders(root_dir)

    if not doing_files:
        doing_files, errors = scan_doing_files(root_dir, stop_dirs)

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
            for _, error in errors:
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
