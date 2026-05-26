"""Tests for query orchestration and execution planning."""

from src.application.orchestration import ExecutionPlanner, QueryOrchestrator
from src.core.router import RouteKind


class _StaticRouter:
    def __init__(self, route: RouteKind):
        self._route = route

    def route(self, _query: str) -> RouteKind:
        return self._route


def _build_orchestrator(route: RouteKind, *, workflow_enabled: bool, is_complex: bool):
    calls = []

    def direct(_query: str) -> str:
        calls.append("direct")
        return "direct"

    def repo(_query: str) -> str:
        calls.append("repo")
        return "repo"

    def workflow(_query: str) -> str:
        calls.append("workflow")
        return "workflow"

    def live(_query: str) -> str:
        calls.append("live")
        return "live"

    orchestrator = QueryOrchestrator(
        router=_StaticRouter(route),
        execution_planner=ExecutionPlanner(),
        run_direct_answer=direct,
        run_repo_code_assistance=repo,
        run_workflow_mode=workflow,
        run_live_troubleshooting=live,
        is_complex_query=lambda _query: is_complex,
        workflow_enabled=lambda: workflow_enabled,
    )
    return orchestrator, calls


def test_orchestrator_direct_answer_route():
    orchestrator, calls = _build_orchestrator(
        RouteKind.DIRECT_ANSWER,
        workflow_enabled=True,
        is_complex=True,
    )

    result = orchestrator.run("summarize this")

    assert result == "direct"
    assert calls == ["direct"]


def test_orchestrator_uses_workflow_for_complex_live_queries():
    orchestrator, calls = _build_orchestrator(
        RouteKind.LIVE_TROUBLESHOOTING,
        workflow_enabled=True,
        is_complex=True,
    )

    result = orchestrator.run("troubleshoot intermittent service mesh issue")

    assert result == "workflow"
    assert calls == ["workflow"]
