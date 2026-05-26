"""Route-aware query orchestration service."""

from typing import Callable

from ...core.interfaces import RouterProtocol
from .execution_planner import ExecutionMode, ExecutionPlanner


class QueryOrchestrator:
    """Orchestrate query execution by route and execution plan."""

    def __init__(
        self,
        *,
        router: RouterProtocol,
        execution_planner: ExecutionPlanner,
        run_direct_answer: Callable[[str], str],
        run_repo_code_assistance: Callable[[str], str],
        run_workflow_mode: Callable[[str], str],
        run_live_troubleshooting: Callable[[str], str],
        is_complex_query: Callable[[str], bool],
        workflow_enabled: Callable[[], bool],
    ):
        self.router = router
        self.execution_planner = execution_planner
        self.run_direct_answer = run_direct_answer
        self.run_repo_code_assistance = run_repo_code_assistance
        self.run_workflow_mode = run_workflow_mode
        self.run_live_troubleshooting = run_live_troubleshooting
        self.is_complex_query = is_complex_query
        self.workflow_enabled = workflow_enabled

    def run(self, query: str) -> str:
        """Run query by selecting and executing an execution mode."""
        route = self.router.route(query)
        plan = self.execution_planner.plan(
            route,
            enable_workflow=self.workflow_enabled(),
            is_complex=self.is_complex_query(query),
        )

        if plan.mode == ExecutionMode.DIRECT_ANSWER:
            return self.run_direct_answer(query)

        if plan.mode == ExecutionMode.REPO_CODE_ASSISTANCE:
            return self.run_repo_code_assistance(query)

        if plan.mode == ExecutionMode.WORKFLOW:
            return self.run_workflow_mode(query)

        return self.run_live_troubleshooting(query)
