import json
import os
import re
import unicodedata

CONFIG_PATH = "config.json"

class ConfigManager:
    def __init__(self, path=CONFIG_PATH):
        self.path = path
        self._needs_migration = False
        self.config = self.load()
        if self._needs_migration:
            self.save()

    def load(self):
        if not os.path.exists(self.path):
            return {"guilds": {}}
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
            if "guilds" not in data:
                # Migrate old flat format to new guild-based structure
                data = {"guilds": {"default": data}}
                self._needs_migration = True
            return data
        except Exception:
            return {"guilds": {}}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, guild_id, key, default=None):
        guild_id = str(guild_id)
        return self.config.get("guilds", {}).get(guild_id, {}).get(key, default)

    def set(self, guild_id, key, value):
        guild_id = str(guild_id)
        self.config.setdefault("guilds", {})
        self.config["guilds"].setdefault(guild_id, {})
        self.config["guilds"][guild_id][key] = value
        self.save()

    def get_key_by_value(self, value):
        for guild_settings in self.config.get("guilds", {}).values():
            for key, val in guild_settings.items():
                if str(val) == str(value):
                    return key
        return None

    def generate_key_from_name(self, name):
        normalized = unicodedata.normalize("NFKD", name)
        ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
        clean = re.sub(r"[^\w]+", "_", ascii_str).strip("_").lower()
        return f"channel_{clean}"
