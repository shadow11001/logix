# GitHub Copilot Instructions

## Project Overview
`Logix` is a Python CLI agent that analyzes system logs using LLMs (via OpenRouter) to detect issues and suggest fixes. It pipeline consists of: Collection -> Analysis (LLM) -> Fix Execution.

## Architecture & Data Flow
- **Entry Point**: `src/main.py` orchestrates the workflow.
- **Collection (`src/collector.py`)**: Retrieves raw logs from `journalctl` (requires systemd) or text files.
  - *Pattern*: Returns string errors starting with "Error" rather than raising exceptions. `main.py` explicitly checks for these error strings.
- **Analysis (`src/analyzer.py`)**:
  - Uses `openai` client to talk to OpenRouter.
  - Enforces JSON output from the LLM via prompt engineering and `response_format`.
  - Manually strips markdown code blocks (```json) before JSON parsing.
- **Execution (`src/fixer.py`)**:
  - Interactively suggests repairs.
  - Uses `subprocess.run(..., shell=True)`. All commands should be treated with caution.

## Critical Developer Workflows
- **Environment**:
  - Must have `.env` file (copied from `.env.example`).
  - Required var: `OPENROUTER_API_KEY`.
- **Execution**:
  - Run from project root to resolve imports correctly:
    ```bash
    python -m src.main --lines 50 --source journalctl
    ```
- **Dependencies**: Managed in `requirements.txt` (key libs: `rich`, `openai`, `python-dotenv`).

## Code Conventions
- **UI library**: Use `rich` for all user interaction (Console, Panel, Confirm). Do not use `print()`.
- **Imports**: Use absolute imports rooted at `src` (e.g., `from src.config import Config`).
- **LLM Prompts**: Always define a strict JSON schema in the system prompt. The application logic depends on keys: `has_issues`, `findings`, `log_entry`, `severity`, `suggested_fix`.

## Common Pitfalls
- **Log Collection Errors**: When modifying `Collector`, ensure error strings are returned (not raised) so `main.py` can display them gracefully.
- **JSON Parsing**: The LLM might wrap JSON in markdown blocks. Ensure `Analyzer` continues to handle this cleanup.
