import json
import os

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.config_path = "settings.json"
        self._last_mtime = 0
        self.defaults = {
            "columns": {
                "title": True,
                "artist": True,
                "album": True,
                "albumartist": True,
                "year": True,
                "genre": True
            },
            "covers": {
                "force_500px": True,
                "source": "iTunes"
            },
            "lyrics": {
                "strict_mode": True,
                "save_lrc": False
            }
        }
        self.config = self.load()
        
    def load(self):
        if not os.path.exists(self.config_path):
            return self.defaults.copy()
        
        try:
            # Update mtime
            self._last_mtime = os.path.getmtime(self.config_path)
            
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_defaults(data, self.defaults)
        except:
            return self.defaults.copy()
            
    def _check_reload(self):
        """Check if file has changed on disk and reload if necessary."""
        if not os.path.exists(self.config_path):
            return
            
        try:
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._last_mtime:
                print(f"Config changed on disk (mtime: {current_mtime} > {self._last_mtime}), reloading...")
                self.config = self.load()
        except OSError:
            pass

    def _merge_defaults(self, data, defaults):
        result = defaults.copy()
        for k, v in data.items():
            if k in result and isinstance(v, dict) and isinstance(result[k], dict):
                result[k] = self._merge_defaults(v, result[k])
            else:
                result[k] = v
        return result
        
    def save(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            # Update mtime after save to prevent immediate reload
            self._last_mtime = os.path.getmtime(self.config_path)
        except Exception as e:
            print(f"Failed to save config: {e}")
            
    def get(self, section, key, default=None):
        self._check_reload()
        val = self.config.get(section)
        if isinstance(val, dict):
            return val.get(key, default)
        return default
        
    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()

    def get_section(self, section):
        self._check_reload()
        return self.config.get(section, {})
