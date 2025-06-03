"""Configuration management for Basic ETL Pipeline."""

import os
from pathlib import Path
import yaml
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default configuration
    config = {
        "input_file": "data/input.csv",
        "output_file": "data/output.csv",
        "delimiter": ",",
        "has_header": True,
        "threshold": 0,
        "sort_column": "value",
        "sort_descending": False
    }
    
    # Load from config file if provided
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    if Path(config_path).exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    # Override with environment variables
    env_mappings = {
        "ETL_INPUT_FILE": "input_file",
        "ETL_OUTPUT_FILE": "output_file",
        "ETL_DELIMITER": "delimiter",
        "ETL_THRESHOLD": "threshold",
        "ETL_SORT_COLUMN": "sort_column"
    }
    
    for env_key, config_key in env_mappings.items():
        if env_value := os.getenv(env_key):
            if config_key == "threshold":
                config[config_key] = float(env_value)
            elif config_key == "has_header" or config_key == "sort_descending":
                config[config_key] = env_value.lower() in ('true', '1', 'yes')
            else:
                config[config_key] = env_value
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["input_file", "output_file"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration: {key}")
    
    # Validate file paths
    input_path = Path(config["input_file"])
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path = Path(config["output_file"])
    output_path.parent.mkdir(parents=True, exist_ok=True)