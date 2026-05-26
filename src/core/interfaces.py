"""Core interfaces for app orchestration components."""

from typing import Protocol

from .router import RouteKind


class RouterProtocol(Protocol):
    """Routing contract used by the agent application service."""

    def route(self, query: str) -> RouteKind:
        ...
