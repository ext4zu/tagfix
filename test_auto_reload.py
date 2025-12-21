import sys
import os
import time
import json

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.config import ConfigManager

def test_auto_reload():
    print("Testing ConfigManager Auto-Reload...")
    
    # 1. Initialize ConfigManager
    cm = ConfigManager()
    
    # Ensure initial state
    cm.set("covers", "force_500px", True)
    initial_val = cm.get("covers", "force_500px")
    print(f"Initial value: {initial_val}")
    
    if initial_val is not True:
        print("FAIL: Initial setup failed.")
        return

    # 2. Modify settings.json externally
    print("Modifying settings.json externally...")
    time.sleep(1.1) # Wait to ensure mtime changes (some filesystems have 1s resolution)
    
    with open("settings.json", 'r') as f:
        data = json.load(f)
        
    data["covers"]["force_500px"] = False
    
    with open("settings.json", 'w') as f:
        json.dump(data, f, indent=4)
        
    # 3. Check if ConfigManager picks up the change
    print("Checking for update...")
    new_val = cm.get("covers", "force_500px")
    print(f"New value: {new_val}")
    
    if new_val is False:
        print("PASS: Auto-reload successful.")
    else:
        print("FAIL: Auto-reload failed.")

if __name__ == "__main__":
    test_auto_reload()
