import subprocess
import os
from pathlib import Path

class LogCollector:
    @staticmethod
    def get_journal_logs(lines: int = 50) -> str:
        """
        Retrieves the last N lines from system journal.
        """
        try:
            # -n: lines, --no-pager: stdout
            command = ["journalctl", "-n", str(lines), "--no-pager"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error retrieving journal logs: {e.stderr}"
        except FileNotFoundError:
            return "Error: journalctl command not found. Are you on a system with systemd?"

    @staticmethod
    def get_file_logs(filepath: str, lines: int = 50) -> str:
        """
        Retrieves the last N lines from a specific log file.
        """
        path = Path(filepath)
        if not path.exists():
            return f"Error: File {filepath} not found."
        
        if not path.is_file():
             return f"Error: {filepath} is not a file."

        try:
            # Using tail to get last N lines efficiently
            command = ["tail", "-n", str(lines), filepath]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            # Fallback for permission errors or other issues
            try:
                with open(filepath, 'r') as f:
                    content = f.readlines()
                    return "".join(content[-lines:])
            except Exception as e2:
                 return f"Error reading file {filepath}: {e} | {e2}"

    @staticmethod
    def read_file(filepath: str) -> str:
        """
        Reads the full content of a configuration file.
        """
        path = Path(filepath)
        if not path.exists():
            return f"Error: File {filepath} not found."
        
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file {filepath}: {str(e)}"
