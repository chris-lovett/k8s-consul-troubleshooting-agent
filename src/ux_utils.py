"""
UX utilities for enhanced terminal output and user interaction.
Implements Phase 4.1 UX improvements.
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich import box
import time

# Global console instance
console = Console()


class RichOutput:
    """Rich terminal output formatting."""
    
    @staticmethod
    def print_header(title: str, subtitle: Optional[str] = None):
        """Print a formatted header."""
        text = Text()
        text.append(title, style="bold cyan")
        if subtitle:
            text.append(f"\n{subtitle}", style="dim")
        
        console.print(Panel(
            text,
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2)
        ))
    
    @staticmethod
    def print_info(message: str, emoji: str = "ℹ️"):
        """Print an info message."""
        console.print(f"{emoji} {message}", style="cyan")
    
    @staticmethod
    def print_success(message: str, emoji: str = "✓"):
        """Print a success message."""
        console.print(f"[green]{emoji} {message}[/green]")
    
    @staticmethod
    def print_warning(message: str, emoji: str = "⚠️"):
        """Print a warning message."""
        console.print(f"[yellow]{emoji} {message}[/yellow]")
    
    @staticmethod
    def print_error(message: str, emoji: str = "❌"):
        """Print an error message."""
        console.print(f"[red]{emoji} {message}[/red]")
    
    @staticmethod
    def print_markdown(content: str):
        """Print markdown-formatted content."""
        md = Markdown(content)
        console.print(md)
    
    @staticmethod
    def print_code(code: str, language: str = "yaml"):
        """Print syntax-highlighted code."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        console.print(syntax)
    
    @staticmethod
    def print_table(data: List[Dict[str, Any]], title: Optional[str] = None):
        """Print a formatted table."""
        if not data:
            console.print("[dim]No data to display[/dim]")
            return
        
        # Get column names from first row
        columns = list(data[0].keys())
        
        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
        
        for col in columns:
            table.add_column(col, style="white")
        
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        console.print(table)
    
    @staticmethod
    def print_status_line(response: str) -> str:
        """Generate a status line based on response content."""
        lowered = response.lower()
        
        if any(word in lowered for word in ["error", "failed", "issue", "problem"]):
            return "[red]⚠️  Issues detected - review the analysis above[/red]"
        elif any(word in lowered for word in ["healthy", "running", "ok", "success"]):
            return "[green]✓ System appears healthy[/green]"
        else:
            return "[yellow]ℹ️  Analysis complete[/yellow]"


class ProgressIndicator:
    """Progress indicators for long-running operations."""
    
    def __init__(self, description: str = "Processing..."):
        self.description = description
        self.progress = None
        self.task_id = None
    
    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        )
        self.progress.__enter__()
        self.task_id = self.progress.add_task(self.description, total=None)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
    
    def update(self, description: str):
        """Update the progress description."""
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=description)


class ErrorFormatter:
    """Format errors with helpful suggestions."""
    
    ERROR_SUGGESTIONS = {
        "403": {
            "title": "Permission Denied",
            "suggestions": [
                "Check your kubeconfig: kubectl config view",
                "Verify namespace access: kubectl auth can-i list pods -n <namespace>",
                "Contact your cluster admin for access"
            ]
        },
        "404": {
            "title": "Resource Not Found",
            "suggestions": [
                "Verify the resource name is correct",
                "Check if the resource exists: kubectl get <resource>",
                "Ensure you're in the correct namespace"
            ]
        },
        "401": {
            "title": "Authentication Failed",
            "suggestions": [
                "Check your kubeconfig credentials",
                "Verify your token hasn't expired",
                "Try: kubectl config use-context <context>"
            ]
        },
        "connection": {
            "title": "Connection Error",
            "suggestions": [
                "Check if the cluster is reachable",
                "Verify your network connection",
                "Ensure kubectl is configured: kubectl cluster-info"
            ]
        },
        "timeout": {
            "title": "Operation Timed Out",
            "suggestions": [
                "The operation took too long to complete",
                "Check cluster health: kubectl get nodes",
                "Try increasing the timeout with --max-time"
            ]
        },
        "openai": {
            "title": "OpenAI API Error",
            "suggestions": [
                "Check your OPENAI_API_KEY environment variable",
                "Verify your API key is valid at platform.openai.com",
                "Check your API usage limits and billing"
            ]
        }
    }
    
    @staticmethod
    def format_error(error: Exception, context: Optional[str] = None) -> str:
        """Format an error with helpful suggestions."""
        error_str = str(error)
        error_type = type(error).__name__
        
        # Detect error category
        category = None
        if "403" in error_str or "Forbidden" in error_str:
            category = "403"
        elif "404" in error_str or "Not Found" in error_str:
            category = "404"
        elif "401" in error_str or "Unauthorized" in error_str:
            category = "401"
        elif "connection" in error_str.lower() or "ConnectionError" in error_type:
            category = "connection"
        elif "timeout" in error_str.lower() or "TimeoutError" in error_type:
            category = "timeout"
        elif "openai" in error_str.lower() or "OpenAI" in error_type:
            category = "openai"
        
        # Build formatted error message
        lines = []
        
        if category and category in ErrorFormatter.ERROR_SUGGESTIONS:
            suggestion = ErrorFormatter.ERROR_SUGGESTIONS[category]
            lines.append(f"[red bold]{suggestion['title']}[/red bold]")
            if context:
                lines.append(f"[dim]{context}[/dim]")
            lines.append("")
            lines.append("[yellow]💡 Try:[/yellow]")
            for i, sug in enumerate(suggestion['suggestions'], 1):
                lines.append(f"   {i}. {sug}")
        else:
            lines.append(f"[red bold]Error: {error_type}[/red bold]")
            if context:
                lines.append(f"[dim]{context}[/dim]")
            lines.append("")
            lines.append(f"[red]{error_str}[/red]")
        
        return "\n".join(lines)


class ConnectionHealthCheck:
    """Pre-flight health checks for connections."""
    
    @staticmethod
    def check_kubernetes() -> tuple[bool, str]:
        """Check Kubernetes connection."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            # Try to get cluster info
            v1.list_namespace(limit=1)
            
            # Get current context
            contexts, active_context = config.list_kube_config_contexts()
            context_name = active_context['name'] if active_context else "unknown"
            
            return True, f"Connected (context: {context_name})"
        except Exception as e:
            return False, f"Failed: {str(e)[:50]}"
    
    @staticmethod
    def check_consul(host: str = "localhost", port: int = 8500) -> tuple[bool, str]:
        """Check Consul connection."""
        try:
            import consul
            c = consul.Consul(host=host, port=port)
            # Try to get leader
            c.status.leader()
            return True, f"Connected ({host}:{port})"
        except Exception as e:
            return False, f"Failed: {str(e)[:50]}"
    
    @staticmethod
    def check_openai() -> tuple[bool, str]:
        """Check OpenAI API connection."""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False, "API key not set"
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Try a minimal API call
            client.models.list()
            return True, "Authenticated"
        except Exception as e:
            return False, f"Failed: {str(e)[:50]}"
    
    @staticmethod
    def run_all_checks(consul_host: str = "localhost", consul_port: int = 8500):
        """Run all health checks and display results."""
        console.print("\n[cyan]🔍 Checking connections...[/cyan]")
        
        # Kubernetes check
        k8s_ok, k8s_msg = ConnectionHealthCheck.check_kubernetes()
        if k8s_ok:
            console.print(f"   [green]✓[/green] Kubernetes cluster: {k8s_msg}")
        else:
            console.print(f"   [red]✗[/red] Kubernetes cluster: {k8s_msg}")
        
        # Consul check
        consul_ok, consul_msg = ConnectionHealthCheck.check_consul(consul_host, consul_port)
        if consul_ok:
            console.print(f"   [green]✓[/green] Consul server: {consul_msg}")
        else:
            console.print(f"   [yellow]⚠[/yellow] Consul server: {consul_msg}")
        
        # OpenAI check
        openai_ok, openai_msg = ConnectionHealthCheck.check_openai()
        if openai_ok:
            console.print(f"   [green]✓[/green] OpenAI API: {openai_msg}")
        else:
            console.print(f"   [red]✗[/red] OpenAI API: {openai_msg}")
        
        console.print()
        
        return k8s_ok and openai_ok


class HelpFormatter:
    """Enhanced help and command documentation."""
    
    @staticmethod
    def show_commands(enable_memory: bool = True, enable_cache: bool = True):
        """Show available commands with descriptions."""
        table = Table(title="Available Commands", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Command", style="green", width=15)
        table.add_column("Description", style="white")
        
        if enable_memory:
            table.add_row("/clear", "Clear conversation memory")
            table.add_row("/history", "Show conversation history")
            table.add_row("/summary", "Show conversation summary")
        
        if enable_cache:
            table.add_row("/cache", "Show cache statistics")
            table.add_row("/clearcache", "Clear session cache")
        
        table.add_row("/help", "Show this help message")
        table.add_row("/examples", "Show common troubleshooting scenarios")
        table.add_row("exit/quit", "End the session")
        
        console.print(table)
        console.print("\n[dim]Type any question to start troubleshooting![/dim]")
    
    @staticmethod
    def show_examples():
        """Show common troubleshooting scenarios."""
        examples = [
            ("Pod Issues", [
                "Why is my pod in CrashLoopBackOff?",
                "Show me pods with high memory usage",
                "Check pod health in namespace production"
            ]),
            ("Service Communication", [
                "Why can't service A connect to service B?",
                "Show service mesh connectivity",
                "Check Consul service health"
            ]),
            ("Resource Problems", [
                "Which nodes are running out of memory?",
                "Show resource limits for all pods",
                "Find pods with insufficient resources"
            ]),
            ("Network Issues", [
                "Are there any network policy issues?",
                "Check if traffic is being blocked",
                "Show service endpoints"
            ])
        ]
        
        console.print(Panel(
            "[bold cyan]Common Troubleshooting Scenarios[/bold cyan]",
            box=box.DOUBLE,
            border_style="cyan"
        ))
        
        for category, questions in examples:
            console.print(f"\n[yellow bold]{category}:[/yellow bold]")
            for i, question in enumerate(questions, 1):
                console.print(f"   {i}. [dim]{question}[/dim]")
        
        console.print("\n[dim]Copy any question above or ask your own![/dim]\n")


# Convenience functions
def print_header(title: str, subtitle: Optional[str] = None):
    """Print a formatted header."""
    RichOutput.print_header(title, subtitle)

def print_success(message: str):
    """Print a success message."""
    RichOutput.print_success(message)

def print_error(message: str):
    """Print an error message."""
    RichOutput.print_error(message)

def print_warning(message: str):
    """Print a warning message."""
    RichOutput.print_warning(message)

def print_info(message: str):
    """Print an info message."""
    RichOutput.print_info(message)

# Made with Bob
