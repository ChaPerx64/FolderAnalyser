import json
import os
from typing import Any

from jsonschema import validate

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

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "searchable_types": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string"
                    }
                },
                "required": ["tag"]
            },
            "minProperties": 1
        },
        "paths": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            },
            "required": [
                "bigfiles_output_path",
                "permissions_output_path",
                "analysis_output_path"
            ]
        }
    },
    "required": ["searchable_types", "paths"]
}

REQUIRED_PATHS = [
    "bigfiles_output_path",
    "permissions_output_path",
    "analysis_output_path",
]


class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def load_config(path: str) -> Any:
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    with open(path, 'r') as f:
        return json.load(f)


def check_config(config: Any) -> None:
    validate(instance=config, schema=CONFIG_SCHEMA)
    check_config_paths(config["paths"])


def check_config_paths(config_paths: dict[str, Any]) -> None:
    for path in REQUIRED_PATHS:
        if path not in config_paths:
            raise ConfigurationError(f"'{path}' is missing in config")
    for path in config_paths.values():
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            raise ConfigurationError(f"Directory in {path} does not exist")

        if not os.access(dir_path, os.W_OK):
            raise ConfigurationError(f"No writing access to {dir_path}")

        if os.path.exists(path) and not os.access(path, os.W_OK):
            raise ConfigurationError(f"No writing access to {path}")


def get_config() -> Any:
    """
    Load the configuration from the CONFIG_PATH file.
    If the file doesn't exist, create it with DEFAULT_CONFIG.

    Returns:
        Any: The loaded configuration as a JSON object.
    """
    config = load_config(CONFIG_PATH)
    check_config(config)
    return config
