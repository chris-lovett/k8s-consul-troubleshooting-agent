"""Tests for pod health query behavior without requiring a live cluster."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.tools.kubernetes import KubernetesTools


@patch("src.tools.kubernetes.config")
@patch("src.tools.kubernetes.client")
def test_list_pods_no_params_uses_default_namespace(mock_client, mock_config):
    """list_pods() should call Kubernetes API with the tool default namespace."""
    mock_config.load_kube_config = Mock()
    mock_client.CoreV1Api = Mock()
    mock_client.AppsV1Api = Mock()

    mock_pod = Mock()
    mock_pod.metadata.name = "web-abc"
    mock_pod.metadata.creation_timestamp = datetime.now(timezone.utc)
    mock_pod.status.phase = "Running"

    mock_container_status = Mock()
    mock_container_status.ready = True
    mock_container_status.restart_count = 0
    mock_pod.status.container_statuses = [mock_container_status]

    v1_instance = mock_client.CoreV1Api.return_value
    v1_instance.list_namespaced_pod.return_value = Mock(items=[mock_pod])

    k8s = KubernetesTools(namespace="default")
    result = k8s.list_pods()

    v1_instance.list_namespaced_pod.assert_called_once_with(namespace="default", label_selector=None)
    assert "Pods in namespace 'default'" in result
    assert "web-abc" in result


@patch("src.tools.kubernetes.config")
@patch("src.tools.kubernetes.client")
def test_list_pods_with_namespace_override(mock_client, mock_config):
    """list_pods(namespace=...) should override the tool default namespace."""
    mock_config.load_kube_config = Mock()
    mock_client.CoreV1Api = Mock()
    mock_client.AppsV1Api = Mock()

    v1_instance = mock_client.CoreV1Api.return_value
    v1_instance.list_namespaced_pod.return_value = Mock(items=[])

    k8s = KubernetesTools(namespace="default")
    result = k8s.list_pods(namespace="prod")

    v1_instance.list_namespaced_pod.assert_called_once_with(namespace="prod", label_selector=None)
    assert "No pods found in namespace 'prod'" in result

