import json
from typing import Dict, Any
from datetime import datetime

class Checkpoint:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save(self, key: str, value: Any) -> None:
        self.data[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f)

    def get(self, key: str) -> Optional[Any]:
        entry = self.data.get(key)
        return entry['value'] if entry else None

    def get_timestamp(self, key: str) -> Optional[datetime]:
        entry = self.data.get(key)
        return datetime.fromisoformat(entry['timestamp']) if entry else None