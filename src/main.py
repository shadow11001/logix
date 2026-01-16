import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from src.config import Config
from src.collector import LogCollector
from src.analyzer import LogAnalyzer
from src.fixer import Fixer
from src.history import HistoryManager
from src.notifier import Notifier
from src.filter import LogFilter
from src.monitor import SystemMonitor

console = Console()

def parse_duration(duration_str) -> int:
    """Converts a duration string (e.g., '10m', '1h') to seconds."""
    if isinstance(duration_str, int):
        return duration_str
        
    duration_str = str(duration_str).strip().lower()
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    # Check for unit suffix
    if duration_str[-1] in multipliers:
        unit = duration_str[-1]
        try:
            value = int(duration_str[:-1])
            return value * multipliers[unit]
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")
    
    # No suffix, assume seconds
    try:
        return int(duration_str)
    except ValueError:
        raise ValueError(f"Invalid duration format: {duration_str}")


def process_log_source(source_name: str, source_path: str, args, log_filter: LogFilter):
    """
    Runs the full analysis pipeline for a single source.
    """
    if not args.cron:
        console.rule(f"[bold cyan]Checking Source: {source_name}[/bold cyan]")
        console.print(f"Path/Command: [dim]{source_path}[/dim]")

    # 1. Collect Logs
    with console.status(f"[bold green]Collecting logs from {source_name}..."):
        if source_path == "journalctl":
            logs = LogCollector.get_journal_logs(args.lines)
        else:
            logs = LogCollector.get_file_logs(source_path, args.lines)

    if not logs or "Error" in logs[:20]: # specific error checks from collector
        if "Error" in logs[:50]:
             console.print(f"[bold red]{logs}[/bold red]")
             return # Skip to next source
        if not logs.strip():
             if not args.cron:
                console.print(f"[bold yellow]No logs found in {source_name}.[/bold yellow]")
             return # Skip to next source
    
    if not args.cron:
        console.print(f"[dim]Collected {len(logs.splitlines())} lines.[/dim]")

    # 2. Filter logs
    original_line_count = len(logs.splitlines())
    logs = log_filter.filter_logs(logs)
    filtered_line_count = len(logs.splitlines())
    
    if original_line_count > filtered_line_count and not args.cron:
        console.print(f"[dim]Filtered {original_line_count - filtered_line_count} ignored lines.[/dim]")

    if not logs.strip():
        if not args.cron:
            console.print(f"[bold green]All logs in {source_name} filtered or empty. No issues.[/bold green]")
        return

    # 3. Keyword check
    if not log_filter.contains_keywords(logs):
        if not args.cron:
            console.print(f"[bold green]No relevant error keywords found in {source_name}. Skipping analysis.[/bold green]")
        return

    # 4. Analyze Logs
    with console.status(f"[bold green]Analyzing {source_name} with AI..."):
        analyzer = LogAnalyzer(Config.OPENROUTER_API_KEY, Config.OPENROUTER_BASE_URL)
        analysis = analyzer.analyze(logs, args.model)

    # 5. Process Results
    has_issues = analysis.get("has_issues")
    findings = analysis.get("findings", [])

    if args.cron:
        if not has_issues:
            return
            
        history = HistoryManager()
        notifier = Notifier()
        
        for finding in findings:
            log_entry = finding.get('log_entry', '')
            severity = finding.get('severity', 'info')
            summary = finding.get('findings', 'Issue detected')
            finding_text = finding.get('explanation', summary)

            if not history.is_duplicate(log_entry):
                console.print(f"New finding detected in {source_name}: {severity}")
                notifier.notify_all(finding)
                history.add_entry(log_entry, severity, finding_text)
            else:
                console.print(f"Duplicate finding skipped: {log_entry[:50]}...")
        return

    # Interactive Mode
    if not has_issues:
        console.print(Panel(f"[bold green]No significant issues found in {source_name}.[/bold green]", title="Analysis Result"))
        return

    console.print(Panel(f"[bold yellow]Issues Detected in {source_name}[/bold yellow]\n\n{analysis.get('summary')}", title="Analysis Result"))
    
    for i, finding in enumerate(findings, 1):
        severity_color = "red" if finding.get('severity') in ['critical', 'error'] else "yellow"
        console.print(f"\n[bold]{i}. Issue ({finding.get('severity')}):[/bold]")
        console.print(f"[dim]Log:[/dim] {finding.get('log_entry')}")
        console.print(f"[bold]Explanation:[/bold] {finding.get('explanation')}")
        
        fix = finding.get("suggested_fix")
        log_entry = finding.get('log_entry', '')
        
        fix_applied = False
        if fix and fix.get("command"):
            if Fixer.apply_fix(fix["command"], fix["description"], fix.get("requires_sudo", False)):
                fix_applied = True
        elif fix:
            console.print(f"[bold blue]Suggestion:[/bold blue] {fix.get('description')}")
            console.print("[dim]No automated command available for this issue.[/dim]")
            
        if not fix_applied:
            if Confirm.ask("Ignore this error in the future?", default=False):
                default_ignore = log_entry.strip()
                pattern = Prompt.ask("Enter pattern to ignore", default=default_ignore)
                log_filter.add_pattern(pattern)
                console.print(f"[green]Added to ignore list.[/green]")

    console.print(f"\n[bold green]Finished checking {source_name}.[/bold green]")
    if args.source == "all":
         Prompt.ask("Press Enter to continue to next log source...")



def main():
    parser = argparse.ArgumentParser(description="AI Agent for PC Log Analysis and Repair")
    parser.add_argument("--model", type=str, help="OpenRouter model to use", default=Config.DEFAULT_MODEL)
    parser.add_argument("--lines", type=int, default=50, help="Number of log lines to analyze")
    parser.add_argument("--source", type=str, default="journalctl", help="Log source: 'journalctl', /path/to/file, 'menu', or 'all'")
    parser.add_argument("--cron", action="store_true", help="Run in cron/headless mode")
    parser.add_argument("--config", type=str, help="Path to a configuration file to analyze")
    parser.add_argument("--generate", type=str, help="Path to save a generated configuration file (requires --prompt)")
    parser.add_argument("--prompt", type=str, help="Custom instruction for analysis or generation")
    parser.add_argument("--show-ignored", action="store_true", help="Show list of ignored patterns")
    parser.add_argument("--monitor", action="store_true", help="Run in System Monitor mode")
    parser.add_argument("--duration", type=str, default="60", help="Monitoring duration (e.g. 60s, 5m, 1h)")
    parser.add_argument("--interval", type=int, default=5, help="Monitoring snapshot interval in seconds (default: 5)")
    
    args = parser.parse_args()

    # Initialize Filter
    log_filter = LogFilter()

    # Handle --show-ignored
    if args.show_ignored:
        patterns = log_filter.get_patterns()
        if patterns:
            console.print(Panel("\n".join(patterns), title="Ignored Patterns", border_style="blue"))
        else:
            console.print("[dim]No ignored patterns found.[/dim]")
        sys.exit(0)

    # 1. Validate Config
    try:
        Config.validate()
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        console.print("Please copy [bold].env.example[/bold] to [bold].env[/bold] and set your API key.")
        sys.exit(1)

    if not args.cron:
        console.print(f"[bold green]Starting Logix[/bold green]")
        console.print(f"Model: [cyan]{args.model}[/cyan]")
    
    if args.monitor:
        monitor = SystemMonitor()
        
        try:
            duration_sec = parse_duration(args.duration)
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

        # 1. Gather Specs
        with console.status("[bold green]Gathering system specifications..."):
            specs = monitor.get_system_specs()
        
        console.print(Panel(
            f"OS: {specs.get('os')} {specs.get('os_release')}\n"
            f"CPU: {specs.get('cpu_count')} cores @ {specs.get('cpu_freq_current')}\n"
            f"RAM: {specs.get('memory_total_gb')} GB\n"
            f"Disk: {specs.get('disk_free_gb')} GB free / {specs.get('disk_total_gb')} GB total",
            title="System Specifications",
            border_style="cyan"
        ))

        # 2. Monitor Loop
        console.print(f"[bold]Monitoring system for {duration_sec} seconds...[/bold]")
        with console.status("[bold green]Tracking performance metrics... (Press Ctrl+C to stop early)"):
            try:
                metrics = monitor.monitor_performance(duration=duration_sec, interval=args.interval)
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring interrupted. Analyzing collected data...[/yellow]")
                metrics = {"error": "Interrupted by user"} # Or implement graceful partial return

        if "error" in metrics and metrics["error"] != "Interrupted by user":
             console.print(f"[bold red]Monitoring Failed:[/bold red] {metrics['error']}")
             sys.exit(1)

        console.print(f"[dim]Collected {len(metrics.get('samples', []))} data points.[/dim]")

        # 3. Collect Recent Logs (Context)
        with console.status("[bold green]Fetching recent system logs for context..."):
            logs = LogCollector.get_journal_logs(lines=50) # Default to journal for context
            # Basic cleanup on context logs
            logs = log_filter.filter_logs(logs)

        # 4. Analyze Health
        with console.status("[bold green]Diagnosing system health with AI..."):
            analyzer = LogAnalyzer(Config.OPENROUTER_API_KEY, Config.OPENROUTER_BASE_URL)
            analysis = analyzer.analyze_health(specs, metrics, logs, args.model)

        # 5. Report
        console.print(Panel(f"[bold]{analysis.get('overall_status', 'Unknown')}[/bold]\n\n{analysis.get('summary')}", title="Health Diagnosis", border_style="green" if analysis.get('overall_status') == "Healthy" else "red"))

        for finding in analysis.get('findings', []):
             severity_color = "red" if finding.get('severity') == 'critical' else "yellow"
             console.print(f"\n[{severity_color}]● {finding.get('issue')} ({finding.get('severity')})[/{severity_color}]")
             console.print(f"  [bold]Evidence:[/bold] {finding.get('evidence')}")
             console.print(f"  [bold]Recommendation:[/bold] {finding.get('recommendation')}")
        
        sys.exit(0)
    # ---------------------------

    # --- Generation Mode ---
    if args.generate:
        if not args.prompt:
            console.print("[bold red]Error:[/bold red] You must provide a --prompt when using --generate.")
            sys.exit(1)
            
        console.rule("[bold cyan]Generating Configuration[/bold cyan]")
        console.print(f"Goal: [dim]{args.prompt}[/dim]")
        
        with console.status(f"[bold green]Generating content for {args.generate}..."):
            analyzer = LogAnalyzer(Config.OPENROUTER_API_KEY, Config.OPENROUTER_BASE_URL)
            result = analyzer.generate_config(args.prompt, args.model)
            
        if "error" in result:
             console.print(f"[bold red]Generation Failed:[/bold red] {result['error']}")
             sys.exit(1)
             
        generated_content = result.get("content", "")
        if not generated_content:
             console.print("[bold red]Generation Failed:[/bold red] No content returned.")
             sys.exit(1)

        console.print(Panel(generated_content, title="Preview", border_style="blue", height=20))
        
        if Confirm.ask(f"Save this content to {args.generate}?", default=False):
            try:
                # Basic check to avoid accidental overwrite without confirmation 
                # (though simple overwrite is standard cli behavior, explicit is safer here)
                path = Path(args.generate)
                if path.exists() and not Confirm.ask(f"[red]File {args.generate} already exists. Overwrite?[/red]", default=False):
                    console.print("[yellow]Save cancelled.[/yellow]")
                    sys.exit(0)
                
                path.write_text(generated_content, encoding="utf-8")
                console.print(f"[bold green]File saved to {args.generate}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Failed to save file:[/bold red] {e}")
        
        sys.exit(0)
    # -----------------------

    # --- Config Check Mode ---
    if args.config:
        console.rule("[bold cyan]Analyzing Configuration[/bold cyan]")
        console.print(f"File: [dim]{args.config}[/dim]")
        if args.prompt:
            console.print(f"Focus: [dim]{args.prompt}[/dim]")

        # 1. Collect
        content = LogCollector.read_file(args.config)
        if content.startswith("Error"):
            console.print(f"[bold red]{content}[/bold red]")
            sys.exit(1)
            
        # 2. Analyze
        with console.status(f"[bold green]Auditing configuration with AI..."):
            analyzer = LogAnalyzer(Config.OPENROUTER_API_KEY, Config.OPENROUTER_BASE_URL)
            analysis = analyzer.analyze_config(content, args.config, args.model, args.prompt)
            
        # 3. Report Results
        has_issues = analysis.get("has_issues", False)
        summary = analysis.get("summary", "Analysis complete.")
        
        border_style = "red" if has_issues else "green"
        console.print(Panel(summary, title="Config Audit Result", border_style=border_style))
        
        findings = analysis.get("findings", [])
        if not findings:
            console.print("[bold green]No issues found. Configuration looks good.[/bold green]")
        else:
            for i, finding in enumerate(findings, 1):
                severity = finding.get('severity', 'info')
                color = "red" if severity in ['critical', 'high'] else "yellow"
                
                console.print(f"\n[{color}][bold]{i}. {finding.get('issue')} ({severity.upper()})[/bold][/{color}]")
                if finding.get('line_number'):
                    console.print(f"   [dim]Line: {finding.get('line_number')}[/dim]")
                if finding.get('parameter'):
                    console.print(f"   [dim]Parameter: {finding.get('parameter')}[/dim]")
                
                console.print(f"   [bold]Suggestion:[/bold] {finding.get('suggestion')}")
                if finding.get('suggested_value'):
                    console.print(f"   [bold blue]Recommended Value:[/bold blue] {finding.get('suggested_value')}")

        sys.exit(0)
    # -------------------------

    # Determine Sources
    sources_to_check = {}

    if args.source == "menu":
        from rich.prompt import Prompt
        console.print("[bold cyan]Available Log Sources:[/bold cyan]")
        options = list(Config.COMMON_LOGS.keys())
        for idx, key in enumerate(options, 1):
            console.print(f"{idx}. {key} [dim]({Config.COMMON_LOGS[key]})[/dim]")
        
        choice = Prompt.ask("Select a log source", choices=[str(i) for i in range(1, len(options) + 1)])
        selected_key = options[int(choice) - 1]
        sources_to_check[selected_key] = Config.COMMON_LOGS[selected_key]

    elif args.source == "all":
        sources_to_check = Config.COMMON_LOGS

    else:
        # Default single source behavior
        name = "Custom File" if args.source != "journalctl" else "System Journal"
        sources_to_check[name] = args.source

    # Run Analysis Loop
    for name, path in sources_to_check.items():
        process_log_source(name, path, args, log_filter)

    if not args.cron:
        console.print("\n[bold green]All checks complete.[/bold green]")

if __name__ == "__main__":
    main()
