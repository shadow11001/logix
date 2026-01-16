import json
import os
from typing import List
from pathlib import Path

class LogFilter:
    IGNORE_FILE = "ignore_patterns.json"
    # Keywords that trigger analysis if found in logs (case-insensitive checks usually)
    TRIGGER_KEYWORDS = ["error", "fail", "warn", "critical", "exception", "fatal"]

    def __init__(self):
        self.ignore_patterns: List[str] = self._load_patterns()

    def _load_patterns(self) -> List[str]:
        if not os.path.exists(self.IGNORE_FILE):
            return []
        try:
            with open(self.IGNORE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_patterns(self):
        try:
            with open(self.IGNORE_FILE, 'w') as f:
                json.dump(self.ignore_patterns, f, indent=4)
        except IOError:
            pass # Handle error appropriately in a real app, maybe log it

    def should_ignore(self, line: str) -> bool:
        """Returns True if the line contains any of the ignore patterns."""
        return any(pattern in line for pattern in self.ignore_patterns)

    def add_pattern(self, pattern: str):
        if pattern and pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
            self.save_patterns()
            
    def get_patterns(self) -> List[str]:
        return self.ignore_patterns
    
    def remove_pattern(self, pattern: str):
         if pattern in self.ignore_patterns:
             self.ignore_patterns.remove(pattern)
             self.save_patterns()

    def filter_logs(self, logs: str) -> str:
        """
        Filters out lines matching ignore patterns.
        Returns the filtered log string.
        """
        filtered_lines = []
        for line in logs.splitlines():
            if not self.should_ignore(line):
                filtered_lines.append(line)
        return "\n".join(filtered_lines)

    def contains_keywords(self, logs: str) -> bool:
        """
        Checks if the logs contain any of the trigger keywords.
        """
        if not logs:
            return False
            
        logs_lower = logs.lower()
        return any(keyword in logs_lower for keyword in self.TRIGGER_KEYWORDS)
