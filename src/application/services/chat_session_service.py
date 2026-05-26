"""Interactive chat session controller for troubleshooting agent CLI."""

from typing import Callable, List

from ...ux_utils import HelpFormatter, RichOutput, console, print_header, print_success, print_warning


class ChatSessionService:
    """Handle interactive chat loop and slash-command routing."""

    def __init__(
        self,
        *,
        enable_memory: bool,
        enable_intent_routing: bool,
        enable_cache: bool,
        enable_workflow: bool,
        workflow_available: bool,
        clear_memory: Callable[[], None],
        get_conversation_history: Callable[[], List],
        get_conversation_summary: Callable[[], str],
        get_cache_stats: Callable[[], str],
        clear_cache: Callable[[], None],
        run_with_spinner: Callable[[str], str],
    ):
        self.enable_memory = enable_memory
        self.enable_intent_routing = enable_intent_routing
        self.enable_cache = enable_cache
        self.enable_workflow = enable_workflow
        self.workflow_available = workflow_available
        self.clear_memory = clear_memory
        self.get_conversation_history = get_conversation_history
        self.get_conversation_summary = get_conversation_summary
        self.get_cache_stats = get_cache_stats
        self.clear_cache = clear_cache
        self.run_with_spinner = run_with_spinner

    def run(self) -> None:
        """Start and manage an interactive troubleshooting chat session."""
        print_header(
            "Kubernetes & Consul Troubleshooting Agent",
            "AI-powered troubleshooting for your service mesh",
        )

        console.print("\n[dim]I'm here to help you troubleshoot Kubernetes and Consul issues.[/dim]\n")

        if self.enable_memory:
            RichOutput.print_info("Conversation memory is ENABLED - I'll remember our discussion!", "💾")

        if self.enable_intent_routing:
            RichOutput.print_info("Intent routing is ENABLED - Fast-path for common issues!", "🚀")

        if self.enable_cache:
            RichOutput.print_info("Session caching is ENABLED - Faster repeated queries!", "⚡")

        if self.enable_workflow and self.workflow_available:
            RichOutput.print_info("LangGraph workflows are ENABLED - Advanced troubleshooting!", "🔄")

        console.print()
        console.print("[dim]Type [bold]/help[/bold] for available commands or [bold]/examples[/bold] for common scenarios.[/dim]")
        console.print("[dim]Type [bold]exit[/bold] or [bold]quit[/bold] to end the session.[/dim]\n")

        while True:
            try:
                user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()

                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("\n[green]Goodbye! Happy troubleshooting! 👋[/green]")
                    break

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self._handle_command(user_input.lower()):
                        continue

                response = self.run_with_spinner(user_input)
                console.print(f"\n[bold blue]Agent:[/bold blue] {response}")
                console.print(RichOutput.print_status_line(response))

            except KeyboardInterrupt:
                console.print("\n\n[green]Goodbye! Happy troubleshooting! 👋[/green]")
                break
            except Exception as e:
                from ...ux_utils import ErrorFormatter

                error_msg = ErrorFormatter.format_error(e, context="During chat session")
                console.print(f"\n{error_msg}")

    def _handle_command(self, command: str) -> bool:
        """Handle slash commands. Returns True when command was handled."""
        if command == "/clear":
            self.clear_memory()
            print_success("Conversation memory cleared.")
            return True

        if command == "/history":
            history = self.get_conversation_history()
            if not history:
                console.print("[dim]No conversation history yet.[/dim]")
            else:
                console.print(f"\n[bold cyan]📜 Conversation History[/bold cyan] [dim]({len(history)} messages)[/dim]:")
                for i, msg in enumerate(history, 1):
                    role = "[green]You[/green]" if msg.type == "human" else "[blue]Agent[/blue]"
                    content = str(msg.content)[:200]
                    if len(str(msg.content)) > 200:
                        content += "..."
                    console.print(f"\n{i}. {role}:")
                    console.print(f"   [dim]{content}[/dim]")
            return True

        if command == "/summary":
            console.print(f"\n[bold cyan]📋 Conversation Summary:[/bold cyan]\n{self.get_conversation_summary()}")
            return True

        if command == "/cache":
            console.print(f"\n{self.get_cache_stats()}")
            return True

        if command == "/clearcache":
            self.clear_cache()
            print_success("Session cache cleared.")
            return True

        if command == "/help":
            HelpFormatter.show_commands(self.enable_memory, self.enable_cache)
            return True

        if command == "/examples":
            HelpFormatter.show_examples()
            return True

        print_warning(f"Unknown command: {command}")
        console.print("[dim]Type [bold]/help[/bold] to see available commands.[/dim]")
        return True
