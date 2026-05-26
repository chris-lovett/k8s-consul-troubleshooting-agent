"""Kubernetes adapter wrapping KubernetesTools."""

from typing import Optional

from ...tools.kubernetes import KubernetesTools


class KubernetesAdapter:
    """Infrastructure adapter for Kubernetes diagnostics access."""

    def __init__(self, tools: KubernetesTools):
        self._tools = tools

    @property
    def namespace(self) -> str:
        return self._tools.namespace

    @property
    def v1(self):
        return self._tools.v1

    def get_pod_status(self, pod_name: str, namespace: Optional[str] = None) -> str:
        return self._tools.get_pod_status(pod_name, namespace)

    def get_pod_logs(
        self,
        pod_name: str,
        namespace: Optional[str] = None,
        container: Optional[str] = None,
        tail_lines: int = 100,
    ) -> str:
        return self._tools.get_pod_logs(pod_name, namespace, container, tail_lines)

    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> str:
        return self._tools.list_pods(namespace, label_selector)

    def describe_pod(self, pod_name: str, namespace: Optional[str] = None) -> str:
        return self._tools.describe_pod(pod_name, namespace)
