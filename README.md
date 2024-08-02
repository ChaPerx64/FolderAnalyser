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

## Testing

The project includes test suites to verify both permission detection and file type detection functionalities. These tests are located in the `/tests/` folder.

### Permission Detection Tests

Located in `/tests/permission_detection_tests/`:

1. `conftest.py`: Contains pytest fixtures that set up the testing environment with temporary files having specific permissions.
2. `test_permission_detection.py`: Contains the actual test cases for permission detection.

These tests verify the correct detection of world-writable files, files with SUID bits set, and files with SGID bits set.

### Type Detection Tests

Located in `/tests/type_detection_tests/`:

1. `test_type_detection.py`: Tests the basic file type detection functionality.
2. `test_thorough_type_detection.py`: Tests the thorough file type detection functionality.
3. `data` directory with sample files

These tests verify the correct detection and categorization of various file types, including Image, Text, Video, Audio, and Application files. They also check for correct file counts and sizes for each category.

### Test Setup

- Permission tests use pytest fixtures to create a temporary directory with files that have various permission settings.
- Type detection tests use a predefined set of files in a `data` directory to verify correct categorization.

### Running the Tests

To run all tests, navigate to the project root directory and execute:

```
pytest
```

Don't forget to install dependencies by running

```
pip install -r requirements_testing.txt 
```


### Key Test Cases

1. Permission Detection:
   - Verify that the correct number of permission warnings (3) is detected.

2. Type Detection:
   - Verify correct categorization of files into Image, Text, Video, Audio, and Application types.
   - Check for accurate file counts and total sizes for each category.
   - Test both basic and thorough detection modes.

3. General:
   - Ensure the analysis output contains the expected structure and data types.
   - Verify that no errors occur during file processing.

These tests ensure that the dir_analyzer correctly identifies and reports files with potentially risky permissions and accurately categorizes files by type.
