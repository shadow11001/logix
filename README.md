# Logix (AI Log Analyzer)

Logix is an intelligent CLI agent that monitors your system health, analyzes logs using Large Language Models (LLMs via OpenRouter), allows you to interactively fix issues, and provides continuous performance monitoring.

It is designed to be a "digital mechanic" for your Linux system, capable of understanding complex error logs, correlating them with system state, and suggesting concrete repair commands.

## Features

*   **🔍 Log Analysis**: deeply analyzes system logs (`journalctl`, `syslog`, `auth.log`, etc.) to find hidden errors and warnings.
*   **🤖 AI-Powered Diagnosis**: Uses advanced LLMs (via OpenRouter) to explain *why* an error occurred, not just *that* it occurred.
*   **🛠️ Interactive Fixes**: Suggests shell commands to fix identified problems and allows you to run them directly from the tool (with confirmation).
*   **asd📉 System Monitoring**: Track CPU, Memory, and Disk usage over time and correlate performance spikes with log errors.
*   **🧠 Intelligent Filtering**: Automatically ignores known "noise" and allows you to teach the AI which patterns to ignore in the future.
*   **⏰ Cron/Headless Mode**: Can run in the background to periodically check logs and send notifications (Discord/Email) only when new issues are found.

## Prerequisites

*   **OS**: Linux (optimized for systemd-based distributions like Ubuntu, Debian, Fedora, Arch).
*   **Python**: 3.8 or higher.
*   **API Key**: An account with [OpenRouter](https://openrouter.ai/) to access LLMs.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/logix.git
    cd logix
    ```

2.  **Set up a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Environment Variables**:
    Copy the example configuration file and edit it:
    ```bash
    cp .env.example .env
    nano .env
    ```

    You **must** set your `OPENROUTER_API_KEY`. You can also configure the default model and notification settings here.

    ```ini
    OPENROUTER_API_KEY=sk-or-your-key-here
    DEFAULT_MODEL=google/gemini-2.0-flash-001
    
    # Optional: For notifications in --cron mode
    DISCORD_WEBHOOK_URL=
    SMTP_SERVER=smtp.gmail.com
    # ... see .env for full list
    ```

2.  **Custom Log Sources** (Optional):
    You can add custom log files to check by creating a `user_logs.json` file in the root directory:
    ```json
    {
        "Nginx Error Log": "/var/log/nginx/error.log",
        "My App Log": "/home/user/myapp/debug.log"
    }
    ```

## Usage

Run the tool from the repository root using `python -m src.main`.

### 1. Interactive Log Analysis (Default)
Check the system journal (journalctl) for recent errors:
```bash
python -m src.main
```

Check a specific file:
```bash
python -m src.main --source /var/log/Xorg.0.log
```

Select from a menu of common logs:
```bash
python -m src.main --source menu
```

Check ALL configured log sources:
```bash
python -m src.main --source all
```

### 2. System Monitoring Mode
Monitor system resources (CPU/RAM) for a specific duration, then analyze logs from that period to find correlations:
```bash
# Monitor for 60 seconds (default)
python -m src.main --monitor

# Monitor for 5 minutes
python -m src.main --monitor --duration 5m
```

### 3. Automated Background Checks (Cron)
Run without user interaction. If issues are found, it uses the configured notification channels (Discord/Email). Useful for daily health checks.
```bash
python -m src.main --cron
```

### 4. Managing Ignored Patterns
If the tool finds an error you don't care about, you can choose to "Ignore" it during the interactive session. To see what you are currently ignoring:
```bash
python -m src.main --show-ignored
```

## CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--source` | Log source to check (`journalctl`, `/path/to/file`, `menu`, `all`) | `journalctl` |
| `--lines` | Number of log lines to analyze | `50` |
| `--model` | Specific OpenRouter model to use | `google/gemini-2.0-flash-001` |
| `--monitor` | specific functionality to run system monitor | `False` |
| `--duration` | Duration for monitoring (e.g., `30s`, `10m`) | `60` |
| `--interval` | Snapshot interval for monitoring in seconds | `5` |
| `--cron` | Run in headless mode (no output unless error found + notifications) | `False` |
| `--show-ignored` | Print the list of ignored log patterns | `False` |

## License

[MIT](LICENSE)

## Disclaimer

This tool uses Generative AI to suggest fixes. While it creates a "human-in-the-loop" workflow by asking for confirmation before running commands, **always review suggested commands carefully**. The authors are not responsible for any damage caused by executing AI-suggested commands.
