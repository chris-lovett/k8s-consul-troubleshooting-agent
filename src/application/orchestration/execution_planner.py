"""Execution planning for routed user queries."""

from dataclasses import dataclass
from enum import Enum

from ...core.router import RouteKind


class ExecutionMode(str, Enum):
    """Available execution modes for a routed query."""

    DIRECT_ANSWER = "direct_answer"
    REPO_CODE_ASSISTANCE = "repo_code_assistance"
    WORKFLOW = "workflow"
    LIVE_TROUBLESHOOTING = "live_troubleshooting"


@dataclass(frozen=True)
class ExecutionPlan:
    """Plan returned by the execution planner."""

    mode: ExecutionMode


class ExecutionPlanner:
    """Decide execution mode from route and runtime feature flags."""

    def plan(self, route: RouteKind, *, enable_workflow: bool, is_complex: bool) -> ExecutionPlan:
        """Build an execution plan for the current query."""
        if route == RouteKind.DIRECT_ANSWER:
            return ExecutionPlan(mode=ExecutionMode.DIRECT_ANSWER)

        if route == RouteKind.REPO_CODE_ASSISTANCE:
            return ExecutionPlan(mode=ExecutionMode.REPO_CODE_ASSISTANCE)

        if enable_workflow and is_complex:
            return ExecutionPlan(mode=ExecutionMode.WORKFLOW)

        return ExecutionPlan(mode=ExecutionMode.LIVE_TROUBLESHOOTING)
