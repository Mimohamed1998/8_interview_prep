"""
Test and demonstrate configuration loading functionality
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.common.utils import load_config, get_config_value, ConfigManager, init_config, get_global_config


def test_load_config():
    """Test loading entire configuration as dictionary"""
    print("\n" + "="*70)
    print("TEST 1: Load Entire Configuration")
    print("="*70)
    
    config = load_config()
    
    print("\nFull configuration dictionary:")
    for section, values in config.items():
        print(f"\n  {section.upper()}:")
        if isinstance(values, dict):
            for key, val in values.items():
                print(f"    {key}: {val}")
        else:
            print(f"    {values}")
    
    return config


def test_get_config_value(config):
    """Test getting nested values using dot notation"""
    print("\n" + "="*70)
    print("TEST 2: Get Config Values with Dot Notation")
    print("="*70)
    
    test_keys = [
        'data.raw_path',
        'data.processed_path',
        'model.random_state',
        'model.test_size',
        'logging.level',
        'visualization.theme',
        'visualization.dpi'
    ]
    
    print("\nAccessing specific configuration values:")
    for key in test_keys:
        value = get_config_value(config, key)
        print(f"  {key}: {value}")
    
    # Test default value for non-existent key
    print("\n  Non-existent key with default:")
    value = get_config_value(config, 'nonexistent.key', default='DEFAULT_VALUE')
    print(f"  nonexistent.key (default='DEFAULT_VALUE'): {value}")


def test_config_manager():
    """Test ConfigManager context manager"""
    print("\n" + "="*70)
    print("TEST 3: ConfigManager Context Manager")
    print("="*70)
    
    print("\nUsing ConfigManager as context manager:")
    with ConfigManager() as config:
        print(f"  Raw data path: {config['data']['raw_path']}")
        print(f"  Test size: {config['model']['test_size']}")
        print(f"  Visualization theme: {config['visualization']['theme']}")
    
    print("\nUsing ConfigManager.get() method:")
    manager = ConfigManager()
    raw_path = manager.get('data.raw_path')
    print(f"  Raw path: {raw_path}")
    
    test_size = manager.get('model.test_size')
    print(f"  Test size: {test_size}")
    
    dpi = manager.get('visualization.dpi', default=100)
    print(f"  DPI: {dpi}")


def test_global_config():
    """Test global configuration instance"""
    print("\n" + "="*70)
    print("TEST 4: Global Configuration Instance")
    print("="*70)
    
    print("\nInitializing global config...")
    config = init_config()
    print(f"  Initialized: {type(config).__name__} with {len(config)} sections")
    
    print("\nAccessing global config:")
    global_config = get_global_config()
    print(f"  Logging level: {global_config['logging']['level']}")
    print(f"  Figsize: {global_config['visualization']['figsize']}")


def main():
    """Run all configuration tests"""
    print("\n" + "="*70)
    print("CONFIGURATION LOADING DEMONSTRATION")
    print("="*70)
    
    try:
        # Test 1: Load config
        config = test_load_config()
        
        # Test 2: Get individual values
        test_get_config_value(config)
        
        # Test 3: ConfigManager
        test_config_manager()
        
        # Test 4: Global config
        test_global_config()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
