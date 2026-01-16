import subprocess
from rich.console import Console
from rich.prompt import Confirm

console = Console()

class Fixer:
    @staticmethod
    def apply_fix(command: str, description: str, requires_sudo: bool = False) -> bool:
        """
        Prompts user and executes a command.
        """
        console.print(f"\n[bold yellow]Suggested Fix:[/bold yellow] {description}")
        console.print(f"[bold cyan]Command:[/bold cyan] {command}")
        
        if requires_sudo:
            console.print("[bold red]Note:[/bold red] This command requires sudo privileges.")

        if Confirm.ask("Do you want to execute this command?"):
            try:
                # If sudo is required, we might just rely on the command string containing 'sudo' 
                # or prepend it if the agent flag it. 
                # Note: The agent might put 'sudo apt update' in the command string itself.
                # Use shell=True for complex commands (pipes etc), but be careful.
                console.print("[dim]Executing...[/dim]")
                
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    console.print("[bold green]Success![/bold green]")
                    console.print(result.stdout)
                    return True
                else:
                    console.print("[bold red]Command Failed:[/bold red]")
                    console.print(result.stderr)
                    return False
            except Exception as e:
                console.print(f"[bold red]Execution Error:[/bold red] {e}")
                return False
        else:
            console.print("[dim]Skipped.[/dim]")
            return False
