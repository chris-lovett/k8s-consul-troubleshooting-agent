"""Tool factory for building LangChain tools with activity tracking and caching."""

from collections import Counter
from typing import Any, Callable, Dict, List, Optional

from langchain.tools import Tool

from ...error_patterns import format_pattern_match, pattern_matcher
from ...session_cache import SessionCache


class ToolFactoryService:
    """Build and wrap troubleshooting tools with shared runtime behavior."""

    def __init__(
        self,
        *,
        k8s_tools: Any,
        consul_tools: Any,
        cache: SessionCache,
        enable_cache: bool,
        verbose: bool,
        get_active_tool_tracker: Callable[[], Optional[Counter]],
        record_active_tool_output: Callable[[Dict[str, str]], None],
    ):
        self.k8s_tools = k8s_tools
        self.consul_tools = consul_tools
        self.cache = cache
        self.enable_cache = enable_cache
        self.verbose = verbose
        self.get_active_tool_tracker = get_active_tool_tracker
        self.record_active_tool_output = record_active_tool_output

    def create_tools(self) -> List[Tool]:
        """Create LangChain tools from Kubernetes, Consul, and pattern services."""
        return [
            Tool(
                name="get_pod_status",
                func=self._wrap_tool_activity(
                    "Checking pod status...",
                    lambda x: self._parse_and_call(self.k8s_tools.get_pod_status, x),
                    tool_name="get_pod_status",
                ),
                description="""Get the status of a specific Kubernetes pod.
                Input REQUIRED: pod_name or pod_name,namespace
                Example: "my-app-pod" or "my-app-pod,production"
                Use this to check if a specific pod is running, pending, or has errors.
                NOTE: To check ALL pods, use list_pods instead.""",
            ),
            Tool(
                name="get_pod_logs",
                func=self._wrap_tool_activity(
                    "Reviewing logs...",
                    lambda x: self._parse_and_call(self.k8s_tools.get_pod_logs, x),
                    tool_name="get_pod_logs",
                ),
                description="""Get logs from a specific Kubernetes pod.
                Input REQUIRED: pod_name or pod_name,namespace or pod_name,namespace,container
                Example: "my-app-pod" or "my-app-pod,production" or "my-app-pod,production,app-container"
                Use this to investigate application errors or crashes in a specific pod.""",
            ),
            Tool(
                name="list_pods",
                func=self._wrap_tool_activity(
                    "Listing pods...",
                    lambda x: self._parse_and_call(self.k8s_tools.list_pods, x),
                    tool_name="list_pods",
                ),
                description="""List all pods in a namespace.
                Input can be: empty (uses default namespace), namespace, or namespace,label_selector
                Example: "" or "default" or "production,app=myapp"
                Use this to see all pods and their status, or to check if all pods are healthy.""",
            ),
            Tool(
                name="describe_pod",
                func=self._wrap_tool_activity(
                    "Inspecting pod details...",
                    lambda x: self._parse_and_call(self.k8s_tools.describe_pod, x),
                    tool_name="describe_pod",
                ),
                description="""Get detailed information about a specific pod (similar to kubectl describe).
                Input REQUIRED: pod_name or pod_name,namespace
                Example: "my-app-pod" or "my-app-pod,production"
                Use this to see events, configuration, and detailed status of a specific pod.""",
            ),
            Tool(
                name="list_consul_services",
                func=self._wrap_tool_activity(
                    "Listing Consul services...",
                    lambda x: self.consul_tools.list_services(),
                    tool_name="list_consul_services",
                ),
                description="""List all services registered in Consul.
                Input: empty string "" (datacenter parameter not currently used)
                Use this to see what services are available in the service mesh.""",
            ),
            Tool(
                name="get_service_health",
                func=self._wrap_tool_activity(
                    "Checking Consul service health...",
                    lambda x: self.consul_tools.get_service_health(x),
                    tool_name="get_service_health",
                ),
                description="""Get health status of a specific Consul service.
                Input REQUIRED: service_name
                Example: "web-service"
                Use this to check if a specific service is healthy and see health check details.""",
            ),
            Tool(
                name="get_service_instances",
                func=self._wrap_tool_activity(
                    "Reviewing service instances...",
                    lambda x: self.consul_tools.get_service_instances(x),
                    tool_name="get_service_instances",
                ),
                description="""Get all instances of a specific Consul service.
                Input REQUIRED: service_name
                Example: "web-service"
                Use this to see where instances of a specific service are running.""",
            ),
            Tool(
                name="list_consul_intentions",
                func=self._wrap_tool_activity(
                    "Listing Consul intentions...",
                    lambda x: self.consul_tools.list_intentions(),
                    tool_name="list_consul_intentions",
                ),
                description="""List all Consul Connect intentions (service-to-service access rules).
                Input: empty string ""
                Use this to see which services can communicate with each other.""",
            ),
            Tool(
                name="check_consul_intention",
                func=self._wrap_tool_activity(
                    "Checking Consul intention...",
                    lambda x: self._parse_and_call(self.consul_tools.check_intention, x),
                    tool_name="check_consul_intention",
                ),
                description="""Check if traffic is allowed between two specific services.
                Input REQUIRED: source_service,destination_service
                Example: "web,api"
                Use this to troubleshoot service-to-service communication issues.""",
            ),
            Tool(
                name="get_consul_members",
                func=self._wrap_tool_activity(
                    "Checking Consul cluster members...",
                    lambda x: self.consul_tools.get_agent_members(),
                    tool_name="get_consul_members",
                ),
                description="""Get Consul cluster members.
                Input: empty string ""
                Use this to check cluster health and member status.""",
            ),
            Tool(
                name="match_error_pattern",
                func=self._wrap_tool_activity(
                    "Analyzing error patterns...",
                    lambda x: self._match_error_pattern(x),
                    tool_name="match_error_pattern",
                ),
                description="""Match error messages or logs against known error patterns for instant diagnosis.
                Input should be: error_text or error_text,category
                Example: "CrashLoopBackOff" or "ImagePullBackOff,kubernetes"
                Category can be 'kubernetes' or 'consul' (optional)
                Use this FIRST when you see error messages or symptoms to get instant solutions.""",
            ),
            Tool(
                name="search_error_patterns",
                func=self._wrap_tool_activity(
                    "Searching error pattern database...",
                    lambda x: self._search_error_patterns(x),
                    tool_name="search_error_patterns",
                ),
                description="""Search the error pattern database by keywords or symptoms.
                Input should be: search_query
                Example: "pod crashing" or "connection refused" or "memory"
                Use this to find relevant error patterns when you know the symptom but not the exact error.""",
            ),
        ]

    def _wrap_tool_activity(self, activity_message: str, func, tool_name: str = ""):
        """Print lightweight tool activity when verbose mode is disabled, with caching support."""

        def wrapped(input_str: str):
            normalized_input = (input_str or "").strip()

            if self.enable_cache and tool_name:
                cached_result = self.cache.get(tool_name, normalized_input)
                if cached_result is not None:
                    if not self.verbose:
                        print(f"\n{activity_message} [cached]", flush=True)
                    return cached_result

            tracker = self.get_active_tool_tracker()
            if tracker is not None:
                tool_key = f"{activity_message}|{normalized_input}"
                tracker[tool_key] += 1
                if tracker[tool_key] > 2:
                    raise RuntimeError(
                        f"Repeated tool call limit reached for '{activity_message}' with the same input."
                    )

            if not self.verbose:
                print(f"\n{activity_message}", flush=True)

            result = func(input_str)

            if self.enable_cache and tool_name:
                self.cache.set(tool_name, result, normalized_input)

            tracker = self.get_active_tool_tracker()
            if tracker is not None:
                rendered_result = str(result).strip()
                if rendered_result:
                    self.record_active_tool_output(
                        {
                            "activity": activity_message,
                            "input": normalized_input,
                            "output": rendered_result[:500],
                        }
                    )

            return result

        return wrapped

    @staticmethod
    def _parse_and_call(func, input_str: str):
        """Parse comma-separated input and call function with appropriate arguments."""
        if not input_str or input_str.strip() == "":
            return func()

        parts = [p.strip() for p in input_str.split(",")]

        try:
            return func(*parts)
        except TypeError as e:
            return f"Error: Invalid input format. {str(e)}"

    @staticmethod
    def _match_error_pattern(input_str: str) -> str:
        """Match error text against known patterns."""
        if not input_str or not input_str.strip():
            return "Error: Please provide error text to match against patterns."

        parts = [p.strip() for p in input_str.split(",", 1)]
        error_text = parts[0]
        category = parts[1] if len(parts) > 1 else None

        if category and category not in ["kubernetes", "consul"]:
            return f"Error: Invalid category '{category}'. Use 'kubernetes' or 'consul'."

        matches = pattern_matcher.match(error_text, category)

        if not matches:
            return (
                "No matching error patterns found in the database. "
                "This might be a unique issue. Proceed with manual troubleshooting using other tools."
            )

        output = [f"Found {len(matches)} matching error pattern(s):\n"]

        for i, pattern in enumerate(matches[:3], 1):
            output.append(f"\n{'=' * 70}")
            output.append(f"Match #{i}: {pattern.name} ({pattern.severity.upper()} severity)")
            output.append("=" * 70)
            output.append(format_pattern_match(pattern))

        if len(matches) > 3:
            output.append(f"\n... and {len(matches) - 3} more pattern(s).")
            output.append("Use search_error_patterns to explore more patterns.")

        return "\n".join(output)

    @staticmethod
    def _search_error_patterns(query: str) -> str:
        """Search error patterns by keywords or symptoms."""
        if not query or not query.strip():
            return "Error: Please provide a search query."

        matches = pattern_matcher.search_patterns(query)

        if not matches:
            return (
                f"No error patterns found matching '{query}'. "
                "Try different keywords like 'crash', 'connection', 'memory', 'certificate', etc."
            )

        output = [f"Found {len(matches)} pattern(s) matching '{query}':\n"]

        for i, pattern in enumerate(matches[:5], 1):
            output.append(f"\n{i}. {pattern.name} ({pattern.category}/{pattern.subcategory})")
            output.append(f"   Severity: {pattern.severity.upper()}")
            output.append(f"   Keywords: {', '.join(pattern.keywords[:5])}")

            if i <= 2:
                output.append("\n   Symptoms:")
                for symptom in pattern.symptoms[:3]:
                    output.append(f"     • {symptom}")
                output.append("\n   Quick Solutions:")
                for solution in pattern.solutions[:2]:
                    output.append(f"     • {solution}")

        if len(matches) > 5:
            output.append(f"\n... and {len(matches) - 5} more pattern(s).")

        output.append("\nUse match_error_pattern with specific error text for detailed diagnosis.")

        return "\n".join(output)
