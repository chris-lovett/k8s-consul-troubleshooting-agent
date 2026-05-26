"""Centralized query routing for execution path selection."""

from enum import Enum
from typing import List


class RouteKind(str, Enum):
    """Supported execution routes."""

    LIVE_TROUBLESHOOTING = "live_troubleshooting"
    REPO_CODE_ASSISTANCE = "repo_code_assistance"
    DIRECT_ANSWER = "direct_answer"


class QueryRouter:
    """Determine the best execution route for a user query."""

    def __init__(self):
        self.live_troubleshooting_keywords: List[str] = [
            "pod", "pods", "kubectl", "kubernetes", "k8s", "namespace",
            "logs", "crashloop", "crashloopbackoff", "service health",
            "consul", "intention", "intentions", "service mesh", "mesh",
            "cluster members", "member", "health check", "service instance",
            "service instances", "registered service", "sidecar",
        ]
        self.repo_code_keywords: List[str] = [
            "file", "files", "function", "class", "method", "module",
            "implement", "implementation", "refactor", "test", "tests",
            "code", "bug", "fix", "patch", "diff", "commit", "readme",
            "documentation", "doc", "agent.py", "requirements.txt",
        ]
        self.direct_answer_keywords: List[str] = [
            "explain", "summarize", "summary", "what does", "why does",
            "git message", "commit message", "name this", "rename",
            "recommend", "suggest", "plan", "roadmap", "what should",
        ]

    def route(self, query: str) -> RouteKind:
        """Route the query to the most appropriate execution mode."""
        normalized = query.lower()

        if any(keyword in normalized for keyword in self.live_troubleshooting_keywords):
            return RouteKind.LIVE_TROUBLESHOOTING
        if any(keyword in normalized for keyword in self.repo_code_keywords):
            return RouteKind.REPO_CODE_ASSISTANCE
        if any(keyword in normalized for keyword in self.direct_answer_keywords):
            return RouteKind.DIRECT_ANSWER
        return RouteKind.DIRECT_ANSWER
