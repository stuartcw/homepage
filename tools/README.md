# Dot Doing: An Automated .doing.md Aggregator

Dot Doing is a Python script that scans a specified directory and its subdirectories for all `.doing.md` files, validates their content, and generates an aggregated Markdown file (`doing.md`). The resulting file provides a structured view of the contents of these `.doing.md` files, sorted by the last modified time.

## Shell Integration

```bash
function chpwd() {
    # Check if the shell is interactive
    if [[ $- == *i* ]]; then
        echo "You have entered: $(pwd)"

        touch .doing.md

        if [[ -s ".doing.md" ]]; then
            presenterm .doing.md
            glow .doing.md
        fi
    fi
}

```


## Features

- **Customizable Root Directory**: Specify the root directory to scan for `.doing.md` files.
- **Skip Unwanted Directories**: Configure which directories to ignore during the scan using environment variables.
- **Content Validation**: Automatically checks the format of each `.doing.md` file to ensure it adheres to specified standards.
- **Real-time Progress Feedback**: Uses a progress bar to indicate the scanning and generation process.
- **Markdown Output**: Compiles results into a well-formatted `doing.md` file that includes a list of entries, each linking back to the source `.doing.md` files.

## Prerequisites

- Python 3.x
- Required Packages:
  - Click
  - python-dotenv
  - alive-progress

These packages can be installed via pip:

```bash
pip install click python-dotenv alive-progress
```

## Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/dot_doing.git
   cd dot_doing
   ```

2. **Create a `.env` File (Optional)**:
   You can define default environment variables in a `.env` file. Below is an example content:
   ```plaintext
   ROOT_DIR=/path/to/your/root/directory
   STOP_DIRS=node_modules,.git,venv
   ```

3. **Running the Script**:
   You can run the script from the command line by providing the root directory:

   ```bash
   python dot_doing.py --root-dir /path/to/your/root/directory
   ```

   Alternatively, if you've set the `ROOT_DIR` variable in the `.env` file, you can simply run:

   ```bash
   python dot_doing.py
   ```

## Functionality Overview

### Load Stop Directories

The script loads a list of directories to skip from an environment variable `STOP_DIRS`, or defaults to a predefined set of directories, including:

- `node_modules`
- `.git`
- `venv`
- Various cache and build directories

### Markdown Anchor Generation

Each `.doing.md` file's relative path is converted to a Markdown-style anchor for easy navigation within `doing.md`.

### Validate `.doing.md` Files

The script checks each `.doing.md` file to ensure it starts with a level 3 header (`###`), and does not contain any other header levels.

### File Aggregation

All valid `.doing.md` files are compiled into a single `doing.md` file, with entries sorted by the last modified time, displaying timestamps and links for easy access.

## Example Output

After running the script, you will find a file named `doing.md` in the specified root directory, formatted like this:

```
# Index of .doing.md Files
Sorted by last modified time (newest first):
- [2023-10-10 14:30] [path/to/file1.doing.md](#path-to-file1-doing-md)
- [2023-10-09 10:15] [path/to/file2.doing.md](#path-to-file2-doing-md)

# Aggregated Content

<a id="path-to-file1-doing-md"></a>
## path/to/file1.doing.md
**Last modified**: 2023-10-10 14:30
(Content of the file)

---

<a id="path-to-file2-doing-md"></a>
## path/to/file2.doing.md
**Last modified**: 2023-10-09 10:15
(Content of the file)

---
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or additional features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Contact

For questions or support, please open an issue in this repository or contact me via [your-email@example.com](mailto:your-email@example.com).

---

Enjoy efficient management of your .doing.md files! Happy coding! 🎉
