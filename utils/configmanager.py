import json
import os
import re
import unicodedata

CONFIG_PATH = "config.json"

class ConfigManager:
    def __init__(self, path=CONFIG_PATH):
        self.path = path
        self.config = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def get_key_by_value(self, value):
        for key, val in self.config.items():
            if str(val) == str(value):
                return key
        return None

    def generate_key_from_name(self, name):
        normalized = unicodedata.normalize("NFKD", name)
        ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
        clean = re.sub(r"[^\w]+", "_", ascii_str).strip("_").lower()
        return f"channel_{clean}"
