import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Logic to check multiple locations for .env
_env_paths = [
    Path.cwd() / ".env",                          # 1. Current directory
    Path.home() / ".config" / "logix" / ".env",   # 2. XDG Config
    Path.home() / ".logix" / ".env",              # 3. Dotfolder in home
    Path(__file__).parent.parent / ".env"         # 4. Source root (for dev)
]

_loaded_path = None
for _path in _env_paths:
    if _path.exists():
        load_dotenv(dotenv_path=_path)
        _loaded_path = _path
        break

# Fallback if nothing specific found
if not _loaded_path:
    load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "google/gemini-2.0-flash-001")
    
    # Notification Config
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM")
    SMTP_TO = os.getenv("SMTP_TO")

    COMMON_LOGS = {
        "System Journal": "journalctl",
        "Syslog": "/var/log/syslog",
        "Auth Log": "/var/log/auth.log",
        "Kernel Log": "/var/log/kern.log",
        "Dmesg": "/var/log/dmesg",
        "Package Manager (dpkg)": "/var/log/dpkg.log",
        "Xorg Log": "/var/log/Xorg.0.log",
    }
    
    # Load user defined logs
    _user_logs_path = Path("user_logs.json")
    if _user_logs_path.exists():
        try:
            with open(_user_logs_path, "r") as f:
                _user_logs = json.load(f)
                if isinstance(_user_logs, dict):
                    COMMON_LOGS.update(_user_logs)
        except Exception as e:
            print(f"Warning: Failed to load user_logs.json: {e}")

    @staticmethod
    def validate():
        if not Config.OPENROUTER_API_KEY:
            paths_str = "\n".join([f"  - {p}" for p in _env_paths])
            raise ValueError(
                f"OPENROUTER_API_KEY not found in environment variables.\n"
                f"Checked the following locations for a .env file:\n{paths_str}\n\n"
                f"Please create ~/.config/logix/.env and add your OPENROUTER_API_KEY."
            )
