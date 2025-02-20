import json
from typing import Optional

class Config:
    def __init__(self, config_file: Optional[str]):
        self._config_file = config_file
        self._config = None
        self.config = self._load_config()

    def _load_config(self):
        try:
            with open(self._config_file, 'r') as config_file:
                config = json.load(config_file)
                return config
        except:
            raise Exception("failed to unpack config")
        return config
            
    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        self._config = config