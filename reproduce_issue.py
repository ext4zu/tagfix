import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.config import ConfigManager
from core.metadata import MetadataHandler

def test_config_singleton():
    print("Testing ConfigManager Singleton...")
    c1 = ConfigManager()
    c2 = ConfigManager()
    
    print(f"c1 ID: {id(c1)}")
    print(f"c2 ID: {id(c2)}")
    
    if c1 is c2:
        print("PASS: ConfigManager is a singleton.")
    else:
        print("FAIL: ConfigManager is NOT a singleton.")
        
    # Test setting value
    print("\nTesting Config Update...")
    c1.set("covers", "force_500px", False)
    val = c2.get("covers", "force_500px")
    print(f"Value in c2 after update in c1: {val}")
    
    if val is False:
        print("PASS: Config update reflected.")
    else:
        print("FAIL: Config update NOT reflected.")

def test_metadata_logic():
    print("\nTesting MetadataHandler Logic...")
    c = ConfigManager()
    c.set("covers", "force_500px", False)
    
    handler = MetadataHandler()
    # We can't easily test fetch_cover without mocking requests, 
    # but we can check if handler.config sees the change.
    
    val = handler.config.get("covers", "force_500px")
    print(f"MetadataHandler config value: {val}")
    
    if val is False:
        print("PASS: MetadataHandler sees correct config.")
    else:
        print("FAIL: MetadataHandler sees WRONG config.")

if __name__ == "__main__":
    test_config_singleton()
    test_metadata_logic()
