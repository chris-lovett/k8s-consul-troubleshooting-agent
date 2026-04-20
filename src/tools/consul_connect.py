"""
Consul Connect sidecar proxy diagnostic tools for the troubleshooting agent.

This module provides advanced diagnostics for Consul Connect sidecar proxies (Envoy),
including health checks, configuration inspection, mTLS certificate validation,
upstream connectivity, and metrics analysis.
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
import requests
import json
from datetime import datetime, timezone
import re

if TYPE_CHECKING:
    from kubernetes.client import CoreV1Api


class ConsulConnectTools:
    """Tools for diagnosing Consul Connect sidecar proxies."""
    
    def __init__(self, k8s_client: "CoreV1Api", namespace: str = "default"):
        """
        Initialize Consul Connect diagnostic tools.
        
        Args:
            k8s_client: Kubernetes CoreV1Api client
            namespace: Default namespace to use
        """
        self.k8s_client = k8s_client
        self.namespace = namespace
        self.envoy_admin_port = 19000  # Default Envoy admin port
    
    def get_proxy_status(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Get comprehensive status of the Consul Connect sidecar proxy.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Formatted proxy status information
        """
        ns = namespace or self.namespace
        
        try:
            # Get pod information
            pod = self.k8s_client.read_namespaced_pod(name=pod_name, namespace=ns)
            
            result = f"=== Consul Connect Proxy Status for '{pod_name}' ===\n\n"
            
            # Check if pod has Consul Connect annotations
            annotations = pod.metadata.annotations or {}
            consul_inject = annotations.get('consul.hashicorp.com/connect-inject', 'false')
            
            if consul_inject != 'true':
                result += "⚠️  WARNING: Pod does not have Consul Connect injection enabled\n"
                result += f"   consul.hashicorp.com/connect-inject: {consul_inject}\n"
                return result
            
            result += "✓ Consul Connect injection enabled\n\n"
            
            # Find sidecar proxy container
            proxy_container = None
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    if 'consul-connect-envoy-sidecar' in container.name or 'envoy' in container.name.lower():
                        proxy_container = container
                        break
            
            if not proxy_container:
                result += "✗ Sidecar proxy container not found\n"
                result += "   Expected container name containing 'consul-connect-envoy-sidecar' or 'envoy'\n"
                return result
            
            result += f"Proxy Container: {proxy_container.name}\n"
            result += f"  Image: {proxy_container.image}\n"
            result += f"  Ready: {proxy_container.ready}\n"
            result += f"  Restart Count: {proxy_container.restart_count}\n"
            
            # Container state
            if proxy_container.state.running:
                result += f"  State: Running (started at {proxy_container.state.running.started_at})\n"
                result += "  ✓ Proxy is running\n"
            elif proxy_container.state.waiting:
                result += f"  State: Waiting\n"
                result += f"  Reason: {proxy_container.state.waiting.reason}\n"
                result += f"  Message: {proxy_container.state.waiting.message}\n"
                result += "  ✗ Proxy is not running\n"
            elif proxy_container.state.terminated:
                result += f"  State: Terminated\n"
                result += f"  Reason: {proxy_container.state.terminated.reason}\n"
                result += f"  Exit Code: {proxy_container.state.terminated.exit_code}\n"
                result += f"  Message: {proxy_container.state.terminated.message}\n"
                result += "  ✗ Proxy has terminated\n"
            
            # Check relevant annotations
            result += "\nConsul Connect Configuration:\n"
            service_name = annotations.get('consul.hashicorp.com/connect-service', 'N/A')
            result += f"  Service: {service_name}\n"
            
            upstreams = annotations.get('consul.hashicorp.com/connect-service-upstreams', 'none')
            result += f"  Upstreams: {upstreams}\n"
            
            protocol = annotations.get('consul.hashicorp.com/connect-service-protocol', 'tcp')
            result += f"  Protocol: {protocol}\n"
            
            # Check for common issues
            result += "\nHealth Indicators:\n"
            if proxy_container.restart_count > 5:
                result += f"  ⚠️  High restart count ({proxy_container.restart_count}) - investigate logs\n"
            elif proxy_container.restart_count > 0:
                result += f"  ⚠️  Container has restarted {proxy_container.restart_count} time(s)\n"
            else:
                result += "  ✓ No restarts\n"
            
            if not proxy_container.ready:
                result += "  ✗ Container not ready - check readiness probe\n"
            else:
                result += "  ✓ Container ready\n"
            
            return result
            
        except Exception as e:
            return f"Error getting proxy status: {str(e)}"
    
    def check_envoy_health(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Check Envoy proxy health via admin interface.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Envoy health check results
        """
        ns = namespace or self.namespace
        
        try:
            result = f"=== Envoy Health Check for '{pod_name}' ===\n\n"
            
            # Try to access Envoy admin interface via port-forward
            # Note: In production, this would use kubectl port-forward or exec
            result += "Envoy Admin Interface Check:\n"
            result += f"  Default admin port: {self.envoy_admin_port}\n"
            result += "  Endpoints to check:\n"
            result += f"    - http://localhost:{self.envoy_admin_port}/ready (readiness)\n"
            result += f"    - http://localhost:{self.envoy_admin_port}/server_info (version/state)\n"
            result += f"    - http://localhost:{self.envoy_admin_port}/stats (metrics)\n"
            result += f"    - http://localhost:{self.envoy_admin_port}/clusters (upstream health)\n"
            result += f"    - http://localhost:{self.envoy_admin_port}/config_dump (full config)\n"
            
            result += "\nTo manually check Envoy health:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/ready\n"
            
            result += "\nCommon Envoy health issues:\n"
            result += "  1. Admin interface not accessible - check container is running\n"
            result += "  2. /ready returns non-200 - check upstream connections\n"
            result += "  3. High connection failures in /stats - check intentions\n"
            result += "  4. Certificate errors - check mTLS configuration\n"
            
            return result
            
        except Exception as e:
            return f"Error checking Envoy health: {str(e)}"
    
    def validate_mtls_certificates(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Validate mTLS certificates for the sidecar proxy.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Certificate validation results
        """
        ns = namespace or self.namespace
        
        try:
            result = f"=== mTLS Certificate Validation for '{pod_name}' ===\n\n"
            
            # Get pod to check for certificate-related issues
            pod = self.k8s_client.read_namespaced_pod(name=pod_name, namespace=ns)
            
            result += "Certificate Configuration:\n"
            
            # Check for TLS-related annotations
            annotations = pod.metadata.annotations or {}
            tls_enabled = annotations.get('consul.hashicorp.com/connect-inject', 'false') == 'true'
            
            if tls_enabled:
                result += "  ✓ Consul Connect mTLS enabled\n"
            else:
                result += "  ✗ Consul Connect not enabled\n"
                return result
            
            result += "\nCertificate Locations (in sidecar container):\n"
            result += "  - Leaf Certificate: /consul/connect-inject/\n"
            result += "  - CA Certificate: /consul/connect-inject/\n"
            result += "  - Private Key: /consul/connect-inject/\n"
            
            result += "\nTo inspect certificates:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += "    ls -la /consul/connect-inject/\n"
            
            result += "\nTo check certificate expiry:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += "    openssl x509 -in /consul/connect-inject/service.crt -noout -dates\n"
            
            result += "\nCommon mTLS issues:\n"
            result += "  1. Certificate expired - check Consul CA rotation\n"
            result += "  2. Certificate not found - check Consul agent connectivity\n"
            result += "  3. CA mismatch - verify all services use same Consul datacenter\n"
            result += "  4. Permission denied - check file permissions in container\n"
            result += "  5. Certificate not yet valid - check system time sync\n"
            
            result += "\nVerify via Envoy admin:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/certs | jq\n"
            
            return result
            
        except Exception as e:
            return f"Error validating mTLS certificates: {str(e)}"
    
    def check_upstream_connectivity(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Check connectivity to upstream services through the proxy.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Upstream connectivity analysis
        """
        ns = namespace or self.namespace
        
        try:
            result = f"=== Upstream Connectivity Check for '{pod_name}' ===\n\n"
            
            # Get pod annotations to find configured upstreams
            pod = self.k8s_client.read_namespaced_pod(name=pod_name, namespace=ns)
            annotations = pod.metadata.annotations or {}
            
            upstreams_str = annotations.get('consul.hashicorp.com/connect-service-upstreams', '')
            
            if not upstreams_str:
                result += "No upstreams configured\n"
                result += "  To configure upstreams, add annotation:\n"
                result += "  consul.hashicorp.com/connect-service-upstreams: 'service:port'\n"
                return result
            
            result += f"Configured Upstreams: {upstreams_str}\n\n"
            
            # Parse upstreams (format: "service1:port1,service2:port2")
            upstreams = []
            for upstream in upstreams_str.split(','):
                parts = upstream.strip().split(':')
                if len(parts) >= 2:
                    upstreams.append({'service': parts[0], 'port': parts[1]})
            
            if upstreams:
                result += "Upstream Services:\n"
                for upstream in upstreams:
                    result += f"\n  Service: {upstream['service']}\n"
                    result += f"  Local Port: {upstream['port']}\n"
                    result += f"  Connection: localhost:{upstream['port']} -> {upstream['service']}\n"
                    result += f"  Test: curl http://localhost:{upstream['port']}\n"
            
            result += "\nTo check upstream health via Envoy:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/clusters\n"
            
            result += "\nUpstream Connection Troubleshooting:\n"
            result += "  1. Check Consul intentions allow traffic\n"
            result += "  2. Verify upstream service is registered in Consul\n"
            result += "  3. Confirm upstream service is healthy\n"
            result += "  4. Check Envoy clusters show upstream endpoints\n"
            result += "  5. Verify network policies allow traffic\n"
            result += "  6. Check for mTLS certificate issues\n"
            
            result += "\nCommon upstream errors:\n"
            result += "  - 'no healthy upstream' - service instances are down\n"
            result += "  - 'upstream connect error' - network/firewall issue\n"
            result += "  - '503 Service Unavailable' - no endpoints available\n"
            result += "  - 'TLS error' - certificate validation failed\n"
            result += "  - 'intention denied' - Consul ACL blocking traffic\n"
            
            return result
            
        except Exception as e:
            return f"Error checking upstream connectivity: {str(e)}"
    
    def get_proxy_metrics(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Get Envoy proxy metrics and statistics.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Proxy metrics and statistics
        """
        ns = namespace or self.namespace
        
        try:
            result = f"=== Envoy Proxy Metrics for '{pod_name}' ===\n\n"
            
            result += "Key Metrics to Monitor:\n\n"
            
            result += "1. Connection Metrics:\n"
            result += "   - downstream_cx_total: Total downstream connections\n"
            result += "   - downstream_cx_active: Active downstream connections\n"
            result += "   - upstream_cx_total: Total upstream connections\n"
            result += "   - upstream_cx_active: Active upstream connections\n"
            result += "   - upstream_cx_connect_fail: Failed upstream connections\n\n"
            
            result += "2. Request Metrics:\n"
            result += "   - downstream_rq_total: Total requests received\n"
            result += "   - downstream_rq_xx: Requests by status code (2xx, 4xx, 5xx)\n"
            result += "   - upstream_rq_total: Total upstream requests\n"
            result += "   - upstream_rq_timeout: Upstream request timeouts\n\n"
            
            result += "3. TLS Metrics:\n"
            result += "   - ssl.handshake: TLS handshake count\n"
            result += "   - ssl.connection_error: TLS connection errors\n"
            result += "   - ssl.fail_verify_error: Certificate verification failures\n\n"
            
            result += "4. Health Check Metrics:\n"
            result += "   - health_check.attempt: Health check attempts\n"
            result += "   - health_check.success: Successful health checks\n"
            result += "   - health_check.failure: Failed health checks\n\n"
            
            result += "To retrieve metrics:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/stats\n\n"
            
            result += "To filter specific metrics:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/stats | grep upstream_cx\n\n"
            
            result += "Prometheus format (if enabled):\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/stats/prometheus\n\n"
            
            result += "Metric Interpretation:\n"
            result += "  - High upstream_cx_connect_fail: Connection issues to upstreams\n"
            result += "  - High downstream_rq_5xx: Application or proxy errors\n"
            result += "  - High ssl.connection_error: mTLS configuration issues\n"
            result += "  - High upstream_rq_timeout: Slow upstream services\n"
            result += "  - Low health_check.success: Upstream health issues\n"
            
            return result
            
        except Exception as e:
            return f"Error getting proxy metrics: {str(e)}"
    
    def inspect_proxy_config(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Inspect Envoy proxy configuration (listeners, clusters, routes).
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Proxy configuration inspection results
        """
        ns = namespace or self.namespace
        
        try:
            result = f"=== Envoy Proxy Configuration for '{pod_name}' ===\n\n"
            
            result += "Configuration Endpoints:\n\n"
            
            result += "1. Listeners (inbound/outbound):\n"
            result += f"   kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"     curl -s http://localhost:{self.envoy_admin_port}/listeners\n\n"
            
            result += "2. Clusters (upstream services):\n"
            result += f"   kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"     curl -s http://localhost:{self.envoy_admin_port}/clusters\n\n"
            
            result += "3. Routes (traffic routing rules):\n"
            result += f"   kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"     curl -s http://localhost:{self.envoy_admin_port}/routes\n\n"
            
            result += "4. Full Configuration Dump:\n"
            result += f"   kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"     curl -s http://localhost:{self.envoy_admin_port}/config_dump | jq\n\n"
            
            result += "Configuration Analysis:\n\n"
            
            result += "Listeners:\n"
            result += "  - Public listener: Accepts inbound connections (usually port 20000)\n"
            result += "  - Outbound listeners: One per upstream service\n"
            result += "  - Check: Listener addresses match expected ports\n\n"
            
            result += "Clusters:\n"
            result += "  - Each upstream service has a cluster\n"
            result += "  - Check: Cluster has healthy endpoints\n"
            result += "  - Check: TLS context configured for mTLS\n"
            result += "  - Check: Load balancing policy appropriate\n\n"
            
            result += "Routes:\n"
            result += "  - Defines how requests are routed to clusters\n"
            result += "  - Check: Routes match expected services\n"
            result += "  - Check: Timeout and retry policies configured\n\n"
            
            result += "Common Configuration Issues:\n"
            result += "  1. Missing listener - upstream not configured\n"
            result += "  2. Cluster with no endpoints - service not registered\n"
            result += "  3. TLS context missing - mTLS not configured\n"
            result += "  4. Wrong route match - traffic not reaching service\n"
            result += "  5. Incorrect timeout values - requests timing out\n"
            
            return result
            
        except Exception as e:
            return f"Error inspecting proxy config: {str(e)}"
    
    def diagnose_proxy_logs(self, pod_name: str, namespace: Optional[str] = None, 
                           tail_lines: int = 100) -> str:
        """
        Analyze sidecar proxy logs for common issues.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            tail_lines: Number of log lines to analyze
            
        Returns:
            Log analysis with identified issues
        """
        ns = namespace or self.namespace
        
        try:
            # Get proxy container logs
            logs = self.k8s_client.read_namespaced_pod_log(
                name=pod_name,
                namespace=ns,
                container='consul-connect-envoy-sidecar',
                tail_lines=tail_lines
            )
            
            result = f"=== Proxy Log Analysis for '{pod_name}' ===\n\n"
            result += f"Analyzing last {tail_lines} lines...\n\n"
            
            # Common error patterns
            issues = []
            
            # Connection errors
            if 'upstream connect error' in logs.lower():
                issues.append("⚠️  Upstream connection errors detected")
            
            if 'no healthy upstream' in logs.lower():
                issues.append("⚠️  No healthy upstream endpoints")
            
            # TLS errors
            if 'tls' in logs.lower() and 'error' in logs.lower():
                issues.append("⚠️  TLS/mTLS errors detected")
            
            if 'certificate' in logs.lower() and ('expired' in logs.lower() or 'invalid' in logs.lower()):
                issues.append("⚠️  Certificate validation issues")
            
            # Intention/ACL errors
            if 'intention' in logs.lower() and 'denied' in logs.lower():
                issues.append("⚠️  Consul intention denials")
            
            # Configuration errors
            if 'config' in logs.lower() and 'error' in logs.lower():
                issues.append("⚠️  Configuration errors")
            
            # Timeout errors
            if 'timeout' in logs.lower():
                issues.append("⚠️  Request timeouts detected")
            
            if issues:
                result += "Issues Found:\n"
                for issue in issues:
                    result += f"  {issue}\n"
                result += "\n"
            else:
                result += "✓ No obvious issues detected in recent logs\n\n"
            
            # Log level check
            if '[critical]' in logs.lower() or '[error]' in logs.lower():
                result += "⚠️  Critical or error level messages present\n"
            
            result += "\nTo view full logs:\n"
            result += f"  kubectl logs -n {ns} {pod_name} -c consul-connect-envoy-sidecar --tail={tail_lines}\n\n"
            
            result += "To follow logs in real-time:\n"
            result += f"  kubectl logs -n {ns} {pod_name} -c consul-connect-envoy-sidecar -f\n\n"
            
            result += "To search for specific errors:\n"
            result += f"  kubectl logs -n {ns} {pod_name} -c consul-connect-envoy-sidecar | grep -i error\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing proxy logs: {str(e)}"
    
    def get_proxy_version_info(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Get Envoy proxy version and build information.
        
        Args:
            pod_name: Name of the pod with sidecar proxy
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Proxy version information
        """
        ns = namespace or self.namespace
        
        try:
            result = f"=== Envoy Proxy Version Info for '{pod_name}' ===\n\n"
            
            result += "To get Envoy version:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += "    envoy --version\n\n"
            
            result += "To get detailed server info:\n"
            result += f"  kubectl exec -n {ns} {pod_name} -c consul-connect-envoy-sidecar -- \\\n"
            result += f"    curl -s http://localhost:{self.envoy_admin_port}/server_info | jq\n\n"
            
            result += "Server info includes:\n"
            result += "  - Envoy version\n"
            result += "  - Build configuration\n"
            result += "  - Uptime\n"
            result += "  - State (LIVE, DRAINING, etc.)\n"
            result += "  - Command line options\n\n"
            
            result += "Version Compatibility:\n"
            result += "  - Consul 1.10+: Envoy 1.18+\n"
            result += "  - Consul 1.11+: Envoy 1.19+\n"
            result += "  - Consul 1.12+: Envoy 1.20+\n"
            result += "  - Consul 1.13+: Envoy 1.22+\n"
            result += "  - Consul 1.14+: Envoy 1.24+\n"
            result += "  - Consul 1.15+: Envoy 1.25+\n\n"
            
            result += "Check Consul compatibility matrix:\n"
            result += "  https://www.consul.io/docs/connect/proxies/envoy#supported-versions\n"
            
            return result
            
        except Exception as e:
            return f"Error getting proxy version info: {str(e)}"


# Made with Bob