"""Adapter implementations for external systems."""

from .kubernetes_adapter import KubernetesAdapter
from .consul_adapter import ConsulAdapter

__all__ = ["KubernetesAdapter", "ConsulAdapter"]
