"""
Main agent implementation using LangChain.
"""

import os
import sys
import threading
import time
import warnings
from collections import Counter
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Suppress urllib3 SSL warnings when SSL verification is disabled
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage

from .tools import KubernetesTools, ConsulTools
from .prompts.system_prompts import SYSTEM_PROMPT, REACT_PROMPT_TEMPLATE
from .intent_classifier import intent_classifier
from .session_cache import SessionCache
from .core.router import QueryRouter
from .core.settings import AppSettings
from .application.orchestration import QueryOrchestrator, ExecutionPlanner
from .application.services import IntentRoutingService, ToolFactoryService
from .infrastructure.adapters import KubernetesAdapter, ConsulAdapter
from .ux_utils import (
    RichOutput, ProgressIndicator, ErrorFormatter, ConnectionHealthCheck,
    HelpFormatter, console, print_header, print_success, print_error,
    print_warning, print_info
)

# Optional Phase 3 workflow support
try:
    from .workflows import TroubleshootingWorkflow
    WORKFLOW_AVAILABLE = True
except ImportError:
    TroubleshootingWorkflow = None
    WORKFLOW_AVAILABLE = False


class TroubleshootingAgent:
    """
    AI agent for troubleshooting Kubernetes and Consul service mesh issues.
    """
    
    def __init__(self,
                 openai_api_key: Optional[str] = None,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.1,
                 k8s_namespace: str = "default",
                 consul_host: str = "localhost",
                 consul_port: int = 8500,
                 consul_token: Optional[str] = None,
                 reasoning_model: Optional[str] = None,
                 verbose: bool = False,
                 enable_memory: bool = True,
                 enable_intent_routing: bool = True,
                 enable_cache: bool = True,
                 enable_workflow: bool = True,
                 cache_ttl: int = 300,
                 cache_max_size: int = 100,
                 max_iterations: int = 35,
                 max_execution_time: int = 300,
                 router: Optional[QueryRouter] = None):
        """
        Initialize the troubleshooting agent.
        
        Args:
            openai_api_key: OpenAI API key (reads from env if not provided)
            model: LLM model to use
            temperature: Temperature for LLM responses
            k8s_namespace: Default Kubernetes namespace
            consul_host: Consul server host
            consul_port: Consul server port
            consul_token: Consul ACL token
            reasoning_model: Optional stronger model for complex troubleshooting
            verbose: Enable verbose logging
            enable_memory: Enable conversation memory (default: True)
            enable_intent_routing: Enable intent classification and fast-path routing (default: True)
            enable_cache: Enable session-scoped caching (default: True)
            enable_workflow: Enable LangGraph workflow mode (default: True, Phase 3)
            cache_ttl: Default cache TTL in seconds (default: 300)
            cache_max_size: Maximum cache entries (default: 100)
            max_iterations: Maximum number of tool calls per query (default: 35)
            max_execution_time: Maximum execution time in seconds (default: 300 = 5 minutes)
        """
        # Load environment variables
        load_dotenv()
        
        # Set up OpenAI - ensure API key is in environment
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        # Set the API key in environment if provided as parameter
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        self.verbose = verbose
        self.reasoning_model = reasoning_model or os.getenv("LLM_REASONING_MODEL")
        self._active_tool_tracker: Optional[Counter] = None
        self._active_tool_outputs: list = []
        self.enable_memory = enable_memory
        self.enable_intent_routing = enable_intent_routing
        self.enable_cache = enable_cache
        self.enable_workflow = enable_workflow
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.router = router or QueryRouter()
        self.execution_planner = ExecutionPlanner()
        
        # Initialize session cache
        self.cache = SessionCache(
            default_ttl=cache_ttl,
            max_size=cache_max_size,
            enabled=enable_cache
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        ) if enable_memory else None
        
        # Initialize LLMs (will automatically use OPENAI_API_KEY from environment)
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature
        )
        self.reasoning_llm = ChatOpenAI(
            model=self.reasoning_model,
            temperature=temperature
        ) if self.reasoning_model else None
        
        # Initialize tools
        raw_k8s_tools = KubernetesTools(namespace=k8s_namespace)
        raw_consul_tools = ConsulTools(
            host=consul_host,
            port=consul_port,
            token=consul_token
        )
        self.k8s_tools = KubernetesAdapter(raw_k8s_tools)
        self.consul_tools = ConsulAdapter(raw_consul_tools)

        # Intent classification and fast-path handling extracted from run().
        self.intent_routing_service = IntentRoutingService(
            classify_intent=intent_classifier.classify,
            should_use_fast_path=intent_classifier.should_use_fast_path,
            execute_fast_path=self._execute_fast_path,
            verbose=self.verbose,
            print_intent_details=self._print_intent_classification,
        )
        
        # Create LangChain tools
        self.tool_factory_service = ToolFactoryService(
            k8s_tools=self.k8s_tools,
            consul_tools=self.consul_tools,
            cache=self.cache,
            enable_cache=self.enable_cache,
            verbose=self.verbose,
            get_active_tool_tracker=lambda: self._active_tool_tracker,
            record_active_tool_output=self._record_active_tool_output,
        )
        self.tools = self.tool_factory_service.create_tools()
        
        # Create agent
        self.agent = self._create_agent()
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=verbose,
            max_iterations=self.max_iterations,
            max_execution_time=self.max_execution_time,
            handle_parsing_errors=True
        )

        # Route-aware orchestration service keeps run() lightweight and testable.
        self.query_orchestrator = QueryOrchestrator(
            router=self.router,
            execution_planner=self.execution_planner,
            run_direct_answer=self._run_direct_answer,
            run_repo_code_assistance=self._run_repo_code_assistance,
            run_workflow_mode=self._run_workflow_mode,
            run_live_troubleshooting=self._run_live_troubleshooting,
            is_complex_query=self._is_complex_troubleshooting_query,
            workflow_enabled=lambda: self.enable_workflow,
        )
        
        # Initialize LangGraph workflow (Phase 3) - only if available
        if enable_workflow and WORKFLOW_AVAILABLE and TroubleshootingWorkflow is not None:
            self.workflow = TroubleshootingWorkflow(
                k8s_tools=self.k8s_tools,
                consul_tools=self.consul_tools,
                llm=self.llm,
                verbose=verbose
            )
        else:
            self.workflow = None
            if enable_workflow and not WORKFLOW_AVAILABLE:
                if verbose:
                    print("Warning: LangGraph workflow mode requested but langgraph is not installed.")
                    print("Install with: pip install langgraph")
                    print("Falling back to standard agent mode.")
    
    def _record_active_tool_output(self, output: Dict[str, str]) -> None:
        """Record tool output snippets for partial diagnosis summaries."""
        self._active_tool_outputs.append(output)
    
    def _create_agent(self):
        """Create the ReAct agent."""
        
        # Create prompt with system message
        prompt = PromptTemplate.from_template(
            SYSTEM_PROMPT + "\n\n" + REACT_PROMPT_TEMPLATE
        )
        
        # Create ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return agent

    def _route_query(self, query: str) -> str:
        """Route the query to the most appropriate execution path."""
        return self.router.route(query).value

    def _print_intent_classification(self, intent) -> None:
        """Render intent classification diagnostics in verbose mode."""
        console.print("\n[cyan][Intent Classification][/cyan]")
        console.print(f"  Type: [yellow]{intent.intent_type.value}[/yellow]")
        console.print(f"  Confidence: [green]{intent.confidence:.0%}[/green]")
        console.print(f"  Priority: [blue]{intent.priority}[/blue]")
        console.print(f"  Entities: {intent.entities}")
        console.print(f"  Suggested Flow: {intent.suggested_flow}")

    def _run_direct_answer(self, query: str) -> str:
        """Answer simple natural-language requests without tools."""
        prompt = (
            "You are a concise technical assistant for Kubernetes, Consul, and Python development tasks. "
            "Answer the user's request directly without using tools. "
            "Do not claim to have checked live cluster state or files unless the user provided that information. "
            "If required context is missing, state exactly what is needed.\n\n"
            f"User request: {query}"
        )
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def _run_repo_code_assistance(self, query: str) -> str:
        """Handle repository/code assistance questions without troubleshooting tools."""
        if any(token in query.lower() for token in ["implement", "patch", "refactor", "change", "update"]):
            prompt = (
                "You are helping with repository and code-assistance tasks. "
                "Provide an implementation-oriented answer with these sections when relevant: "
                "Approach, Files to update, Risks, and Next step. "
                "Do not pretend you inspected files or ran commands unless that context is already present. "
                "If file inspection is required, say so explicitly.\n\n"
                f"User request: {query}"
            )
        else:
            prompt = (
                "You are helping with repository and code-assistance tasks. "
                "Answer directly from the user's provided context. "
                "Do not pretend you inspected files or ran commands unless that context is already present. "
                "Provide practical implementation guidance, code reasoning, or concise recommendations. "
                "If file inspection is required, say so explicitly.\n\n"
                f"User request: {query}"
            )
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def _build_partial_diagnosis(self) -> str:
        """Build a concise partial diagnosis from collected tool outputs."""
        if not self._active_tool_outputs:
            return (
                "I couldn't complete a diagnosis within the current limits and didn't gather enough evidence yet. "
                "Try a narrower question or rerun with --verbose."
            )

        summarized_outputs = []
        seen = set()
        for item in self._active_tool_outputs:
            key = (item["activity"], item["input"], item["output"])
            if key in seen:
                continue
            seen.add(key)
            summary_line = f"- {item['activity']}"
            if item["input"]:
                summary_line += f" (input: {item['input']})"
            summary_line += f": {item['output']}"
            summarized_outputs.append(summary_line)
            if len(summarized_outputs) >= 3:
                break

        summary_block = "\n".join(summarized_outputs)
        return (
            "I wasn't able to finish a full diagnosis within the current execution limits, but here's what I found so far:\n"
            f"{summary_block}\n\n"
            "Try narrowing the question to one workload, service, or namespace for a deeper follow-up."
        )

    def _is_complex_troubleshooting_query(self, query: str) -> bool:
        """Determine whether a troubleshooting request should use the stronger reasoning model."""
        normalized = query.lower()
        complexity_signals = [
            "intermittent", "multi-step", "across namespaces", "service mesh",
            "connectivity", "root cause", "timeline", "multiple services",
            "consul intentions", "sidecar", "ingress", "egress", "mtls"
        ]
        return len(query.split()) > 25 or sum(signal in normalized for signal in complexity_signals) >= 2

    def _run_workflow_mode(self, query: str) -> str:
        """
        Run troubleshooting using LangGraph workflow (Phase 3).
        
        This provides:
        - State-based workflow management
        - Parallel tool execution
        - Conditional routing based on issue type
        - Automated remediation suggestions
        """
        if not self.workflow:
            return self._run_live_troubleshooting(query)
        
        try:
            if self.verbose:
                print("\n[Phase 3] Running LangGraph workflow mode...")
            
            # Execute the workflow
            final_state = self.workflow.run(query)
            
            # Format the results
            output = []
            output.append("=== Troubleshooting Analysis (LangGraph Workflow) ===\n")
            
            # Show execution path
            if "execution_path" in final_state:
                output.append(f"Workflow Path: {' → '.join(final_state['execution_path'])}\n")
            
            # Show root cause
            if "root_cause" in final_state:
                output.append(f"Root Cause:\n{final_state['root_cause']}\n")
            
            # Show remediation steps
            if "remediation_steps" in final_state and final_state["remediation_steps"]:
                output.append("\nRemediation Steps:")
                for i, step in enumerate(final_state["remediation_steps"][:5], 1):
                    output.append(f"{i}. {step}")
                output.append("")
            
            # Show automated fixes if available
            if "automated_fixes" in final_state and final_state["automated_fixes"]:
                output.append("\nAutomated Fix Suggestions:")
                for fix in final_state["automated_fixes"]:
                    output.append(f"  • {fix['pattern']}: {fix['description']}")
                    if fix.get('safe', False):
                        output.append(f"    (Safe to automate)")
                output.append("")
            
            # Show execution time
            if "workflow_start_time" in final_state and "workflow_end_time" in final_state:
                duration = (final_state["workflow_end_time"] - final_state["workflow_start_time"]).total_seconds()
                output.append(f"\nWorkflow completed in {duration:.2f} seconds")
            
            return "\n".join(output)
            
        except Exception as e:
            if self.verbose:
                print(f"[Phase 3] Workflow error: {e}, falling back to standard agent")
            return self._run_live_troubleshooting(query)
    
    def _run_live_troubleshooting(self, query: str) -> str:
        """Run the full troubleshooting agent executor."""
        self._active_tool_tracker = Counter()
        self._active_tool_outputs = []

        executor = self.agent_executor
        if self.reasoning_llm and self._is_complex_troubleshooting_query(query):
            reasoning_agent = create_react_agent(
                llm=self.reasoning_llm,
                tools=self.tools,
                prompt=PromptTemplate.from_template(
                    SYSTEM_PROMPT + "\n\n" + REACT_PROMPT_TEMPLATE
                )
            )
            executor = AgentExecutor(
                agent=reasoning_agent,
                tools=self.tools,
                memory=self.memory,
                verbose=self.verbose,
                max_iterations=self.max_iterations,
                max_execution_time=self.max_execution_time,
                handle_parsing_errors=True
            )

        try:
            result = executor.invoke({"input": query})
            return self._format_agent_output(result["output"])
        except RuntimeError as e:
            if "Repeated tool call limit reached" in str(e):
                return self._build_partial_diagnosis()
            raise
        finally:
            self._active_tool_tracker = None
    
    def _execute_fast_path(self, query: str, intent) -> str:
        """
        Execute a fast-path troubleshooting flow based on classified intent.
        
        Args:
            query: User query
            intent: Classified intent object
        
        Returns:
            Diagnosis and recommendations
        """
        if not self.verbose:
            print(f"\n🚀 Fast-path routing: {intent.suggested_flow}", flush=True)
            print(f"   Confidence: {intent.confidence:.0%} | Priority: {intent.priority}", flush=True)
        
        flow = intent_classifier.get_flow(intent.intent_type)
        if not flow:
            # Fallback to standard agent
            return self._run_live_troubleshooting(query)
        
        results = []
        results.append(f"# {flow.name}")
        results.append(f"*{flow.description}*\n")
        
        # Execute each step in the flow
        for step in flow.steps:
            tool_name = step["tool"]
            param_template = step["param"]
            
            # Resolve parameters from entities
            param = self._resolve_flow_parameters(param_template, intent.entities, query)
            
            # Find and execute the tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if not tool:
                results.append(f"\n⚠️ Tool '{tool_name}' not found, skipping...")
                continue
            
            try:
                if not self.verbose:
                    print(f"   → Executing: {tool_name}", flush=True)
                
                result = tool.func(param)
                results.append(f"\n## Step: {tool.description}")
                results.append(f"```\n{result}\n```")
            except Exception as e:
                results.append(f"\n⚠️ Error executing {tool_name}: {str(e)}")
        
        # Add summary
        results.append(f"\n---")
        results.append(f"**Fast-path execution completed** ({flow.expected_duration})")
        results.append(f"Intent: {intent.intent_type.value} (confidence: {intent.confidence:.0%})")
        
        return "\n".join(results)
    
    def _resolve_flow_parameters(self, param_template: str, entities: Dict[str, str], query: str) -> str:
        """
        Resolve flow parameters from entities and query.
        
        Args:
            param_template: Parameter template (e.g., "pod_name", "source,destination")
            entities: Extracted entities
            query: Original query
        
        Returns:
            Resolved parameter string
        """
        if not param_template:
            return ""
        
        # Split template into parts
        parts = [p.strip() for p in param_template.split(',')]
        resolved = []
        alias_map = {
            "source": "source_service",
            "destination": "destination_service",
        }
        
        for part in parts:
            if part in entities:
                # Direct entity match
                resolved.append(entities[part])
            elif part in alias_map and alias_map[part] in entities:
                resolved.append(entities[alias_map[part]])
            elif part == "error_text":
                # Extract error text from query or entities
                if "error_text" in entities:
                    resolved.append(entities["error_text"])
                else:
                    # Use the whole query as error text
                    resolved.append(query)
            elif part == "status_condition":
                # Extract status condition from query
                resolved.append(query)
            else:
                # Try to find in query or use empty
                resolved.append("")
        
        return ",".join(resolved)
    
    def clear_cache(self):
        """Clear the session cache."""
        if self.cache:
            self.cache.clear()
            if self.verbose:
                print("Session cache cleared.")
    
    def get_cache_stats(self) -> str:
        """
        Get cache statistics.
        
        Returns:
            Formatted cache statistics
        """
        if not self.cache:
            return "Caching is disabled for this session."
        
        return self.cache.get_summary()
    
    def invalidate_cache(self, tool_name: Optional[str] = None, pattern: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            tool_name: Invalidate all entries for this tool (optional)
            pattern: Invalidate entries matching this pattern (optional)
        """
        if self.cache:
            self.cache.invalidate(tool_name=tool_name, pattern=pattern)
            if self.verbose:
                if tool_name:
                    print(f"Cache invalidated for tool: {tool_name}")
                elif pattern:
                    print(f"Cache invalidated for pattern: {pattern}")
    
    def clear_memory(self):
        """Clear the conversation memory."""
        if self.memory:
            self.memory.clear()
            if self.verbose:
                print("Conversation memory cleared.")
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """
        Get the conversation history.
        
        Returns:
            List of conversation messages
        """
        if not self.memory:
            return []
        
        return self.memory.chat_memory.messages
    
    def get_conversation_summary(self) -> str:
        """
        Get a human-readable summary of the conversation history.
        
        Returns:
            Formatted conversation history
        """
        if not self.memory:
            return "Memory is disabled for this session."
        
        messages = self.get_conversation_history()
        if not messages:
            return "No conversation history yet."
        
        summary = []
        for i, msg in enumerate(messages, 1):
            role = "User" if msg.type == "human" else "Agent"
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary.append(f"{i}. {role}: {content}")
        
        return "\n".join(summary)
    
    def save_context(self, inputs: Dict[str, str], outputs: Dict[str, str]):
        """
        Manually save context to memory (useful for non-agent interactions).
        
        Args:
            inputs: Input dictionary with 'input' key
            outputs: Output dictionary with 'output' key
        """
        if self.memory:
            self.memory.save_context(inputs, outputs)
    
    def _format_agent_output(self, output: str) -> str:
        """Replace generic executor stop messages with friendlier language."""
        generic_message = "Agent stopped due to iteration limit or time limit."
        fallback_message = (
            "I couldn't complete a diagnosis within the current limits and didn't gather enough evidence yet. "
            "Try a narrower question or rerun with --verbose."
        )

        if output.strip() == generic_message:
            return self._build_partial_diagnosis()

        if generic_message in output:
            replacement = self._build_partial_diagnosis()
            if "didn't gather enough evidence yet" in replacement:
                return replacement
            return replacement
        return output

    def _status_line_for_response(self, response: str) -> str:
        """Generate a short final status line for CLI output."""
        lowered = response.lower()
        if lowered.startswith("error running agent:"):
            return "Status: Unable to complete diagnosis"
        if "didn't gather enough evidence yet" in lowered:
            return "Status: Unable to complete diagnosis"
        if "wasn't able to finish a full diagnosis within the current execution limits" in lowered:
            return "Status: Partial diagnosis (execution limit reached)"
        return "Status: Diagnosis complete"

    def run(self, query: str) -> str:
        """
        Run the agent with an appropriately routed execution path.
        
        Args:
            query: The troubleshooting question or issue description
            
        Returns:
            Agent's response with diagnosis and recommendations
        """
        try:
            if self.enable_intent_routing:
                fast_path_response = self.intent_routing_service.try_fast_path(query)
                if fast_path_response is not None:
                    return fast_path_response
            
            # Fall back to route-aware orchestration.
            return self.query_orchestrator.run(query)
        except Exception as e:
            message = str(e)
            if "iteration limit" in message.lower() or "time limit" in message.lower():
                return self._build_partial_diagnosis()
            # Use enhanced error formatting
            error_msg = ErrorFormatter.format_error(e, context="While processing your query")
            console.print(error_msg)
            return f"Error running agent: {message}"
    
    def _run_with_spinner(self, query: str) -> str:
        """Run the agent while showing a rich progress indicator in interactive mode."""
        response_holder: Dict[str, str] = {"response": ""}
        
        def worker():
            response_holder["response"] = self.run(query)
        
        with ProgressIndicator("🤔 Analyzing your query...") as progress:
            worker_thread = threading.Thread(target=worker)
            worker_thread.start()
            worker_thread.join()
        
        return response_holder["response"] or "Error running agent: No response was produced."

    def chat(self):
        """
        Start an interactive chat session with the agent.
        """
        # Print header with rich formatting
        print_header(
            "Kubernetes & Consul Troubleshooting Agent",
            "AI-powered troubleshooting for your service mesh"
        )
        
        console.print("\n[dim]I'm here to help you troubleshoot Kubernetes and Consul issues.[/dim]\n")
        
        # Show enabled features
        if self.enable_memory:
            RichOutput.print_info("Conversation memory is ENABLED - I'll remember our discussion!", "💾")
        
        if self.enable_intent_routing:
            RichOutput.print_info("Intent routing is ENABLED - Fast-path for common issues!", "🚀")
        
        if self.enable_cache:
            RichOutput.print_info("Session caching is ENABLED - Faster repeated queries!", "⚡")
        
        if self.enable_workflow and WORKFLOW_AVAILABLE:
            RichOutput.print_info("LangGraph workflows are ENABLED - Advanced troubleshooting!", "🔄")
        
        console.print()
        
        # Show available commands
        console.print("[dim]Type [bold]/help[/bold] for available commands or [bold]/examples[/bold] for common scenarios.[/dim]")
        console.print("[dim]Type [bold]exit[/bold] or [bold]quit[/bold] to end the session.[/dim]\n")
        
        while True:
            try:
                user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("\n[green]Goodbye! Happy troubleshooting! 👋[/green]")
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.startswith('/'):
                    if user_input.lower() == '/clear':
                        self.clear_memory()
                        print_success("Conversation memory cleared.")
                        continue
                    elif user_input.lower() == '/history':
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
                        continue
                    elif user_input.lower() == '/summary':
                        console.print(f"\n[bold cyan]📋 Conversation Summary:[/bold cyan]\n{self.get_conversation_summary()}")
                        continue
                    elif user_input.lower() == '/cache':
                        console.print(f"\n{self.get_cache_stats()}")
                        continue
                    elif user_input.lower() == '/clearcache':
                        self.clear_cache()
                        print_success("Session cache cleared.")
                        continue
                    elif user_input.lower() == '/help':
                        HelpFormatter.show_commands(self.enable_memory, self.enable_cache)
                        continue
                    elif user_input.lower() == '/examples':
                        HelpFormatter.show_examples()
                        continue
                    else:
                        print_warning(f"Unknown command: {user_input}")
                        console.print("[dim]Type [bold]/help[/bold] to see available commands.[/dim]")
                        continue
                
                response = self._run_with_spinner(user_input)
                console.print(f"\n[bold blue]Agent:[/bold blue] {response}")
                console.print(RichOutput.print_status_line(response))
                
            except KeyboardInterrupt:
                console.print("\n\n[green]Goodbye! Happy troubleshooting! 👋[/green]")
                break
            except Exception as e:
                error_msg = ErrorFormatter.format_error(e, context="During chat session")
                console.print(f"\n{error_msg}")


def main():
    """Main entry point for the agent."""
    import argparse
    
    # Load environment variables early so they're available for health checks
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Kubernetes & Consul Troubleshooting Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  meshtrbl                                    # Start interactive chat
  meshtrbl --setup                            # Run configuration wizard
  meshtrbl --query "why is my pod failing?"   # Single query mode
  meshtrbl --no-cache --verbose               # Disable cache, enable verbose
  meshtrbl --help                             # Show this help
        """
    )
    parser.add_argument("--setup", action="store_true", help="Run interactive configuration wizard")
    parser.add_argument("--model", default=None, help="OpenAI model to use")
    parser.add_argument("--reasoning-model", help="Optional stronger model for complex live troubleshooting")
    parser.add_argument("--namespace", default=None, help="Default Kubernetes namespace")
    parser.add_argument("--consul-host", default=None, help="Consul server host")
    parser.add_argument("--consul-port", type=int, default=None, help="Consul server port")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--query", help="Single query to run (non-interactive mode)")
    parser.add_argument("--no-memory", action="store_true", help="Disable conversation memory")
    parser.add_argument("--no-intent-routing", action="store_true", help="Disable intent classification and fast-path routing")
    parser.add_argument("--no-cache", action="store_true", help="Disable session-scoped caching")
    parser.add_argument("--no-health-check", action="store_true", help="Skip connection health checks on startup")
    parser.add_argument("--cache-ttl", type=int, default=None, help="Cache TTL in seconds (default: 300)")
    parser.add_argument("--cache-size", type=int, default=None, help="Maximum cache entries (default: 100)")
    parser.add_argument("--max-iterations", type=int, default=None, help="Maximum tool calls per query (default: 35)")
    parser.add_argument("--max-time", type=int, default=None, help="Maximum execution time in seconds (default: 300)")
    
    args = parser.parse_args()
    
    # Run setup wizard if requested
    if args.setup:
        from .config_wizard import ConfigWizard
        ConfigWizard.run_setup()
        return
    
    # Try to load configuration from file
    from .config_wizard import ConfigWizard
    saved_config = ConfigWizard.load_config()
    settings = AppSettings.from_sources(args=args, saved_config=saved_config)
    
    # Run health checks unless disabled
    if not settings.no_health_check:
        health_ok = ConnectionHealthCheck.run_all_checks(settings.consul_host, settings.consul_port)
        if not health_ok:
            print_warning("Some connections failed. The agent may not work correctly.")
            console.print("[dim]Use --no-health-check to skip these checks.[/dim]\n")
    
    try:
        # Create agent
        agent = TroubleshootingAgent(
            model=settings.model,
            reasoning_model=settings.reasoning_model,
            k8s_namespace=settings.namespace,
            consul_host=settings.consul_host,
            consul_port=settings.consul_port,
            verbose=settings.verbose,
            enable_memory=settings.enable_memory,
            enable_intent_routing=settings.enable_intent_routing,
            enable_cache=settings.enable_cache,
            cache_ttl=settings.cache_ttl,
            cache_max_size=settings.cache_size,
            max_iterations=settings.max_iterations,
            max_execution_time=settings.max_time,
            router=QueryRouter(),
        )
        
        # Run in appropriate mode
        if settings.query:
            # Single query mode
            response = agent.run(settings.query)
            console.print(response)
            console.print(RichOutput.print_status_line(response))
        else:
            # Interactive chat mode
            agent.chat()
    
    except Exception as e:
        error_msg = ErrorFormatter.format_error(e, context="Failed to start agent")
        console.print(f"\n{error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
