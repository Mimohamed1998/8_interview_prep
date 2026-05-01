"""
Configuration loader module
Loads YAML configuration files and provides access as dictionaries
"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file. 
                    If None, uses default location (conf/conf.yml)
    
    Returns:
        Dictionary containing configuration data
    
    Raises:
        FileNotFoundError: If configuration file is not found
        yaml.YAMLError: If configuration file is malformed
    """
    if config_path is None:
        # Default path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / "conf" / "conf.yml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config if config is not None else {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing configuration file: {e}")


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a nested value from configuration dictionary using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path to the value (e.g., 'data.raw_path')
        default: Default value if key is not found
    
    Returns:
        The configuration value or default if not found
    
    Example:
        >>> config = load_config()
        >>> raw_path = get_config_value(config, 'data.raw_path')
    """
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


class ConfigManager:
    """
    Context manager for configuration handling.
    Provides convenient access to configuration values.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = None
    
    def __enter__(self) -> Dict[str, Any]:
        """Load configuration on context entry."""
        self.config = load_config(self.config_path)
        return self.config
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit."""
        self.config = None
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key_path: Dot-separated path to the value
            default: Default value if key is not found
        
        Returns:
            The configuration value or default
        """
        if self.config is None:
            self.config = load_config(self.config_path)
        return get_config_value(self.config, key_path, default)


# Global configuration instance
_config_instance = None


def init_config(config_path: str = None) -> Dict[str, Any]:
    """
    Initialize global configuration instance.
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        Configuration dictionary
    """
    global _config_instance
    _config_instance = load_config(config_path)
    return _config_instance


def get_global_config() -> Dict[str, Any]:
    """
    Get the global configuration instance.
    Must call init_config() first.
    
    Returns:
        Configuration dictionary
    
    Raises:
        RuntimeError: If init_config() has not been called
    """
    global _config_instance
    if _config_instance is None:
        raise RuntimeError("Configuration not initialized. Call init_config() first.")
    return _config_instance
