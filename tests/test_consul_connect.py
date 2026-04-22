"""
Tests for Consul Connect sidecar proxy diagnostic tools.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from kubernetes.client import V1Pod, V1ObjectMeta, V1PodStatus, V1ContainerStatus, V1ContainerState, V1ContainerStateRunning, V1ContainerStateWaiting, V1PodSpec
from src.tools.consul_connect import ConsulConnectTools


@pytest.fixture
def mock_k8s_client():
    """Create a mock Kubernetes client."""
    return Mock()


@pytest.fixture
def consul_connect_tools(mock_k8s_client):
    """Create ConsulConnectTools instance with mock client."""
    return ConsulConnectTools(mock_k8s_client, namespace="default")


class TestProxyStatusCheck:
    """Tests for get_proxy_status method."""
    
    def test_proxy_status_with_injection_enabled(self, consul_connect_tools, mock_k8s_client):
        """Test proxy status when Consul Connect injection is enabled."""
        # Create mock pod with Consul Connect annotations
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={
                    "consul.hashicorp.com/connect-inject": "true",
                    "consul.hashicorp.com/connect-service": "web",
                    "consul.hashicorp.com/connect-service-upstreams": "api:8080"
                }
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus(
                container_statuses=[
                    V1ContainerStatus(
                        name="consul-connect-envoy-sidecar",
                        image="envoyproxy/envoy:v1.24.0",
                        ready=True,
                        restart_count=0,
                        state=V1ContainerState(
                            running=V1ContainerStateRunning(started_at="2024-01-01T00:00:00Z")
                        )
                    )
                ]
            )
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.get_proxy_status("test-pod")
        
        assert "Consul Connect injection enabled" in result
        assert "Proxy Container: consul-connect-envoy-sidecar" in result
        assert "State: Running" in result
        assert "✓ Proxy is running" in result
        assert "Service: web" in result
        assert "Upstreams: api:8080" in result
    
    def test_proxy_status_without_injection(self, consul_connect_tools, mock_k8s_client):
        """Test proxy status when Consul Connect injection is not enabled."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus()
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.get_proxy_status("test-pod")
        
        assert "WARNING: Pod does not have Consul Connect injection enabled" in result
    
    def test_proxy_status_container_not_ready(self, consul_connect_tools, mock_k8s_client):
        """Test proxy status when sidecar container is not ready."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={"consul.hashicorp.com/connect-inject": "true"}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus(
                container_statuses=[
                    V1ContainerStatus(
                        name="consul-connect-envoy-sidecar",
                        image="envoyproxy/envoy:v1.24.0",
                        ready=False,
                        restart_count=3,
                        state=V1ContainerState(
                            waiting=V1ContainerStateWaiting(
                                reason="CrashLoopBackOff",
                                message="Back-off restarting failed container"
                            )
                        )
                    )
                ]
            )
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.get_proxy_status("test-pod")
        
        assert "State: Waiting" in result
        assert "Reason: CrashLoopBackOff" in result
        assert "✗ Proxy is not running" in result
        assert "Container has restarted 3 time(s)" in result
        assert "✗ Container not ready" in result


class TestEnvoyHealthCheck:
    """Tests for check_envoy_health method."""
    
    def test_envoy_health_check_instructions(self, consul_connect_tools):
        """Test that health check provides proper instructions."""
        result = consul_connect_tools.check_envoy_health("test-pod")
        
        assert "Envoy Health Check" in result
        assert "Default admin port: 19000" in result
        assert "/ready" in result
        assert "/server_info" in result
        assert "/stats" in result
        assert "/clusters" in result
        assert "kubectl exec" in result


class TestMTLSValidation:
    """Tests for validate_mtls_certificates method."""
    
    def test_mtls_validation_with_connect_enabled(self, consul_connect_tools, mock_k8s_client):
        """Test mTLS validation when Consul Connect is enabled."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={"consul.hashicorp.com/connect-inject": "true"}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus()
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.validate_mtls_certificates("test-pod")
        
        assert "mTLS Certificate Validation" in result
        assert "✓ Consul Connect mTLS enabled" in result
        assert "Certificate Locations" in result
        assert "/consul/connect-inject/" in result
        assert "openssl x509" in result
        assert "Common mTLS issues" in result
    
    def test_mtls_validation_without_connect(self, consul_connect_tools, mock_k8s_client):
        """Test mTLS validation when Consul Connect is not enabled."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus()
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.validate_mtls_certificates("test-pod")
        
        assert "✗ Consul Connect not enabled" in result


class TestUpstreamConnectivity:
    """Tests for check_upstream_connectivity method."""
    
    def test_upstream_connectivity_with_upstreams(self, consul_connect_tools, mock_k8s_client):
        """Test upstream connectivity check with configured upstreams."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={
                    "consul.hashicorp.com/connect-service-upstreams": "api:8080,database:5432"
                }
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus()
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.check_upstream_connectivity("test-pod")
        
        assert "Configured Upstreams: api:8080,database:5432" in result
        assert "Service: api" in result
        assert "Local Port: 8080" in result
        assert "Service: database" in result
        assert "Local Port: 5432" in result
        assert "Upstream Connection Troubleshooting" in result
    
    def test_upstream_connectivity_without_upstreams(self, consul_connect_tools, mock_k8s_client):
        """Test upstream connectivity check without configured upstreams."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus()
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        result = consul_connect_tools.check_upstream_connectivity("test-pod")
        
        assert "No upstreams configured" in result
        assert "To configure upstreams" in result


class TestProxyMetrics:
    """Tests for get_proxy_metrics method."""
    
    def test_proxy_metrics_instructions(self, consul_connect_tools):
        """Test that proxy metrics provides comprehensive instructions."""
        result = consul_connect_tools.get_proxy_metrics("test-pod")
        
        assert "Envoy Proxy Metrics" in result
        assert "Key Metrics to Monitor" in result
        assert "Connection Metrics" in result
        assert "downstream_cx_total" in result
        assert "upstream_cx_total" in result
        assert "Request Metrics" in result
        assert "TLS Metrics" in result
        assert "Health Check Metrics" in result
        assert "To retrieve metrics" in result
        assert "kubectl exec" in result
        assert "/stats" in result


class TestProxyConfigInspection:
    """Tests for inspect_proxy_config method."""
    
    def test_proxy_config_inspection(self, consul_connect_tools):
        """Test proxy configuration inspection instructions."""
        result = consul_connect_tools.inspect_proxy_config("test-pod")
        
        assert "Envoy Proxy Configuration" in result
        assert "Configuration Endpoints" in result
        assert "Listeners" in result
        assert "Clusters" in result
        assert "Routes" in result
        assert "Full Configuration Dump" in result
        assert "/config_dump" in result
        assert "Common Configuration Issues" in result


class TestProxyLogAnalysis:
    """Tests for diagnose_proxy_logs method."""
    
    def test_proxy_log_analysis_with_errors(self, consul_connect_tools, mock_k8s_client):
        """Test proxy log analysis when errors are present."""
        logs = """
        [2024-01-01 00:00:00] [info] Starting Envoy proxy
        [2024-01-01 00:00:01] [error] upstream connect error
        [2024-01-01 00:00:02] [warning] no healthy upstream
        [2024-01-01 00:00:03] [error] TLS handshake failed
        [2024-01-01 00:00:04] [critical] certificate expired
        """
        
        mock_k8s_client.read_namespaced_pod_log.return_value = logs
        
        result = consul_connect_tools.diagnose_proxy_logs("test-pod")
        
        assert "Proxy Log Analysis" in result
        assert "Issues Found" in result
        assert "Upstream connection errors detected" in result
        assert "No healthy upstream endpoints" in result
        assert "TLS/mTLS errors detected" in result
        assert "Certificate validation issues" in result
    
    def test_proxy_log_analysis_without_errors(self, consul_connect_tools, mock_k8s_client):
        """Test proxy log analysis when no errors are present."""
        logs = """
        [2024-01-01 00:00:00] [info] Starting Envoy proxy
        [2024-01-01 00:00:01] [info] Proxy started successfully
        [2024-01-01 00:00:02] [info] Listening on port 20000
        """
        
        mock_k8s_client.read_namespaced_pod_log.return_value = logs
        
        result = consul_connect_tools.diagnose_proxy_logs("test-pod")
        
        assert "✓ No obvious issues detected in recent logs" in result


class TestProxyVersionInfo:
    """Tests for get_proxy_version_info method."""
    
    def test_proxy_version_info(self, consul_connect_tools):
        """Test proxy version information instructions."""
        result = consul_connect_tools.get_proxy_version_info("test-pod")
        
        assert "Envoy Proxy Version Info" in result
        assert "envoy --version" in result
        assert "/server_info" in result
        assert "Version Compatibility" in result
        assert "Consul 1.10+" in result
        assert "Consul 1.15+" in result
        assert "compatibility matrix" in result


class TestErrorHandling:
    """Tests for error handling in Consul Connect tools."""
    
    def test_proxy_status_with_exception(self, consul_connect_tools, mock_k8s_client):
        """Test proxy status handles exceptions gracefully."""
        mock_k8s_client.read_namespaced_pod.side_effect = Exception("API error")
        
        result = consul_connect_tools.get_proxy_status("test-pod")
        
        assert "Error getting proxy status" in result
        assert "API error" in result
    
    def test_mtls_validation_with_exception(self, consul_connect_tools, mock_k8s_client):
        """Test mTLS validation handles exceptions gracefully."""
        mock_k8s_client.read_namespaced_pod.side_effect = Exception("API error")
        
        result = consul_connect_tools.validate_mtls_certificates("test-pod")
        
        assert "Error validating mTLS certificates" in result
    
    def test_upstream_check_with_exception(self, consul_connect_tools, mock_k8s_client):
        """Test upstream connectivity check handles exceptions gracefully."""
        mock_k8s_client.read_namespaced_pod.side_effect = Exception("API error")
        
        result = consul_connect_tools.check_upstream_connectivity("test-pod")
        
        assert "Error checking upstream connectivity" in result
    
    def test_log_analysis_with_exception(self, consul_connect_tools, mock_k8s_client):
        """Test log analysis handles exceptions gracefully."""
        mock_k8s_client.read_namespaced_pod_log.side_effect = Exception("API error")
        
        result = consul_connect_tools.diagnose_proxy_logs("test-pod")
        
        assert "Error analyzing proxy logs" in result


class TestNamespaceHandling:
    """Tests for namespace parameter handling."""
    
    def test_uses_default_namespace(self, consul_connect_tools, mock_k8s_client):
        """Test that default namespace is used when not specified."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="default",
                annotations={"consul.hashicorp.com/connect-inject": "true"}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus(container_statuses=[])
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        consul_connect_tools.get_proxy_status("test-pod")
        
        mock_k8s_client.read_namespaced_pod.assert_called_with(
            name="test-pod",
            namespace="default"
        )
    
    def test_uses_specified_namespace(self, consul_connect_tools, mock_k8s_client):
        """Test that specified namespace overrides default."""
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name="test-pod",
                namespace="production",
                annotations={"consul.hashicorp.com/connect-inject": "true"}
            ),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus(container_statuses=[])
        )
        
        mock_k8s_client.read_namespaced_pod.return_value = pod
        
        consul_connect_tools.get_proxy_status("test-pod", namespace="production")
        
        mock_k8s_client.read_namespaced_pod.assert_called_with(
            name="test-pod",
            namespace="production"
        )


# Made with Bob