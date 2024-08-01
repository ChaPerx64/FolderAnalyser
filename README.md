# Directory Analyzer

Directory Analyzer is a Python-based tool for analyzing file systems. It provides detailed information about file types, sizes, and potential permission issues within a specified directory.
It was developed as a technical test.

## Features

- Analyze file types and sizes within a directory and its subdirectories
- Detect potential permission issues
- Identify large files based on a configurable size threshold
- Generate a summary report of file types and sizes
- Option for thorough mimetype detection
- Configurable output paths for analysis results

## Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`:
  - humanize==4.10.0
  - typer==0.12.3
  - jsonschema==4.23

## Installation

1. Clone this repository
2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script using the following command:

```
python dir_analyzer.py [OPTIONS] DIR_PATH
```

### Arguments

- `DIR_PATH`: Path to the directory that needs to be analyzed

### Options

- `--thorough`: Detect mimetype based on content (default: False)
- `--to-file`: Write analysis results into a file (default: False)
- `--size-threshold FLOAT`: File size in GiB that gets the file marked as big (default: 1)
- `--no-estimate`: Skip counting files for time estimate and progress bar (default: False)

## Configuration

The tool uses a configuration file (`config.json`) to define searchable file types and output paths. If the file doesn't exist, a default configuration will be created.

## Output

The tool generates:
- A summary table of file types and sizes
- A list of large files (written to a file specified in the configuration)
- A list of permission warnings (written to a file specified in the configuration)

## Examples

Analyze a directory with default settings:
```
python dir_analyzer.py /path/to/directory
```

Analyze a directory with thorough mimetype detection and custom size threshold:
```
python dir_analyzer.py --thorough --size-threshold 2.5 /path/to/directory
```
