"""Core interfaces for app orchestration components."""

from typing import Any, Optional, Protocol, runtime_checkable

from .router import RouteKind


@runtime_checkable
class RouterProtocol(Protocol):
    """Routing contract used by the agent application service."""

    def route(self, query: str) -> RouteKind:
        ...


@runtime_checkable
class QueryOrchestratorProtocol(Protocol):
    """Application orchestration contract for query execution."""

    def run(self, query: str) -> str:
        ...


@runtime_checkable
class KubernetesAdapterProtocol(Protocol):
    """Infrastructure contract for Kubernetes diagnostics operations."""

    @property
    def v1(self) -> Any:
        ...

    def get_pod_status(self, pod_name: str, namespace: Optional[str] = None) -> str:
        ...

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: Optional[str] = None,
        container: Optional[str] = None,
        tail_lines: int = 100,
    ) -> str:
        ...

    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> str:
        ...

    def describe_pod(self, pod_name: str, namespace: Optional[str] = None) -> str:
        ...


@runtime_checkable
class ConsulAdapterProtocol(Protocol):
    """Infrastructure contract for Consul diagnostics operations."""

    def list_services(self, datacenter: Optional[str] = None) -> str:
        ...

    def get_service_health(self, service_name: str, datacenter: Optional[str] = None) -> str:
        ...

    def get_service_instances(self, service_name: str, datacenter: Optional[str] = None) -> str:
        ...

    def list_intentions(self) -> str:
        ...

    def check_intention(self, source_service: str, destination_service: str) -> str:
        ...

    def get_agent_members(self) -> str:
        ...
