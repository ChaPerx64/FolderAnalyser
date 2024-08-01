import json
import os
from typing import Any

CONFIG_PATH = "./config.json"

DEFAULT_CONFIG = {
    "searchable_types": {
        "Image": {
            "tag": "image/",
        },
        "Text": {
            "tag": "text/",
        },
        "Audio": {
            "tag": "audio/",
        },
        "Video": {
            "tag": "video/",
        },
        "Application": {
            "tag": "application/",
        },
    },
    "paths": {
        "bigfiles_output_path": "./bigfiles.txt",
        "permissions_output_path": "./permissions.txt",
        "analysis_output_path": "./output.txt",
    }
}


def get_config() -> Any:
    """
    Load the configuration from the CONFIG_PATH file.
    If the file doesn't exist, create it with DEFAULT_CONFIG.

    Returns:
        Any: The loaded configuration as a JSON object.
    """
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)
