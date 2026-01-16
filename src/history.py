import json
import hashlib
import os
from datetime import datetime, timedelta

class HistoryManager:
    def __init__(self, history_file="data/history.json"):
        self.history_file = history_file
        self.ensure_data_dir()
        self.history = self.load()

    def ensure_data_dir(self):
        directory = os.path.dirname(self.history_file)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def load(self):
        if not os.path.exists(self.history_file):
            return {"history": []}
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"history": []}

    def save(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _get_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def is_duplicate(self, finding_text, hours=24):
        """
        Check if a finding (by hash of its text) has occurred within the last `hours`.
        """
        finding_hash = self._get_hash(finding_text)
        cutoff = datetime.now() - timedelta(hours=hours)

        for entry in self.history.get("history", []):
            if entry["id"] == finding_hash:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > cutoff:
                    return True
        return False

    def add_entry(self, finding_text, severity, summary):
        finding_hash = self._get_hash(finding_text)
        entry = {
            "id": finding_hash,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "summary": summary
        }
        self.history.setdefault("history", []).append(entry)
        self.save()

    def prune(self, days=30):
        cutoff = datetime.now() - timedelta(days=days)
        new_history = [
            entry for entry in self.history.get("history", [])
            if datetime.fromisoformat(entry["timestamp"]) > cutoff
        ]
        self.history["history"] = new_history
        self.save()
