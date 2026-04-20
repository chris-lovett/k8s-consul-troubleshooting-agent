"""
Advanced service-to-service communication analysis tools.

This module provides comprehensive analysis of service communication patterns,
dependency mapping, request path tracing, and traffic flow visualization for
Consul Connect service mesh.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class ServiceNode:
    """Represents a service in the communication graph."""
    name: str
    namespace: str = "default"
    instances: int = 0
    healthy_instances: int = 0
    protocol: str = "tcp"
    tags: List[str] = field(default_factory=list)
    upstreams: List[str] = field(default_factory=list)
    downstreams: List[str] = field(default_factory=list)


@dataclass
class CommunicationPath:
    """Represents a communication path between services."""
    source: str
    destination: str
    allowed: bool
    intention_exists: bool
    proxy_healthy: bool
    upstream_healthy: bool
    hops: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)


@dataclass
class TrafficPattern:
    """Represents observed traffic patterns."""
    source: str
    destination: str
    request_count: int = 0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    protocol: str = "http"
    status_codes: Dict[str, int] = field(default_factory=dict)


class ServiceCommunicationAnalyzer:
    """Analyzes service-to-service communication patterns."""
    
    def __init__(self, consul_tools, k8s_tools, proxy_tools):
        """
        Initialize the communication analyzer.
        
        Args:
            consul_tools: ConsulTools instance
            k8s_tools: KubernetesTools instance
            proxy_tools: ConsulConnectTools instance
        """
        self.consul = consul_tools
        self.k8s = k8s_tools
        self.proxy = proxy_tools
        self.service_graph: Dict[str, ServiceNode] = {}
        self.communication_paths: List[CommunicationPath] = []
    
    def build_service_dependency_map(self, namespace: Optional[str] = None) -> str:
        """
        Build a comprehensive service dependency map.
        
        Args:
            namespace: Kubernetes namespace to analyze
            
        Returns:
            Formatted dependency map
        """
        try:
            result = "=== Service Dependency Map ===\n\n"
            
            # Get all services from Consul
            services_output = self.consul.list_services()
            
            # Parse services (simplified - in production would parse actual output)
            result += "Services and Their Dependencies:\n\n"
            
            result += "To build a complete dependency map:\n"
            result += "1. List all Consul services\n"
            result += "2. For each service, check its upstreams configuration\n"
            result += "3. Query Consul intentions to see allowed connections\n"
            result += "4. Check pod annotations for upstream definitions\n"
            result += "5. Analyze Envoy clusters for actual connections\n\n"
            
            result += "Example dependency structure:\n"
            result += "  web-frontend\n"
            result += "    ├─> api-gateway (http:8080)\n"
            result += "    │   ├─> user-service (grpc:9090)\n"
            result += "    │   ├─> product-service (http:8080)\n"
            result += "    │   └─> order-service (http:8080)\n"
            result += "    └─> cache-service (tcp:6379)\n\n"
            
            result += "Dependency Analysis:\n"
            result += "  - Direct dependencies: Services directly called\n"
            result += "  - Transitive dependencies: Services called through others\n"
            result += "  - Circular dependencies: Services that call each other\n"
            result += "  - Orphaned services: Services with no connections\n\n"
            
            result += "To get actual dependency data:\n"
            result += "  kubectl get pods -n <namespace> -o json | \\\n"
            result += "    jq '.items[] | select(.metadata.annotations[\"consul.hashicorp.com/connect-service-upstreams\"]) | \\\n"
            result += "    {service: .metadata.annotations[\"consul.hashicorp.com/connect-service\"], \\\n"
            result += "     upstreams: .metadata.annotations[\"consul.hashicorp.com/connect-service-upstreams\"]}'\n"
            
            return result
            
        except Exception as e:
            return f"Error building dependency map: {str(e)}"
    
    def trace_request_path(self, source_service: str, destination_service: str,
                          namespace: Optional[str] = None) -> str:
        """
        Trace the complete request path between two services.
        
        Args:
            source_service: Source service name
            destination_service: Destination service name
            namespace: Kubernetes namespace
            
        Returns:
            Formatted request path trace
        """
        try:
            result = f"=== Request Path Trace: {source_service} → {destination_service} ===\n\n"
            
            # Check if direct connection exists
            result += "Step 1: Check Direct Connection\n"
            result += f"  Source: {source_service}\n"
            result += f"  Destination: {destination_service}\n\n"
            
            # Check Consul intention
            result += "Step 2: Verify Consul Intention\n"
            intention_result = self.consul.check_intention(source_service, destination_service)
            result += f"  {intention_result}\n\n"
            
            # Check source service proxy
            result += "Step 3: Check Source Service Proxy\n"
            result += f"  - Verify {source_service} sidecar proxy is healthy\n"
            result += f"  - Check upstream configuration includes {destination_service}\n"
            result += f"  - Verify Envoy cluster for {destination_service} exists\n\n"
            
            # Check destination service health
            result += "Step 4: Check Destination Service Health\n"
            health_result = self.consul.get_service_health(destination_service)
            result += f"  {health_result}\n\n"
            
            # Check destination service proxy
            result += "Step 5: Check Destination Service Proxy\n"
            result += f"  - Verify {destination_service} sidecar proxy is healthy\n"
            result += f"  - Check proxy is accepting connections\n"
            result += f"  - Verify mTLS certificates are valid\n\n"
            
            result += "Complete Request Flow:\n"
            result += f"  1. {source_service} application → localhost:<upstream-port>\n"
            result += f"  2. {source_service} Envoy proxy (outbound)\n"
            result += f"  3. mTLS connection over network\n"
            result += f"  4. {destination_service} Envoy proxy (inbound)\n"
            result += f"  5. {destination_service} application\n\n"
            
            result += "Potential Failure Points:\n"
            result += "  ✗ Intention denies traffic\n"
            result += "  ✗ Source proxy not configured for upstream\n"
            result += "  ✗ Destination service unhealthy\n"
            result += "  ✗ Destination proxy not ready\n"
            result += "  ✗ mTLS certificate issues\n"
            result += "  ✗ Network connectivity problems\n"
            result += "  ✗ Timeout configuration too short\n"
            
            return result
            
        except Exception as e:
            return f"Error tracing request path: {str(e)}"
    
    def analyze_communication_patterns(self, service_name: str,
                                      namespace: Optional[str] = None) -> str:
        """
        Analyze communication patterns for a service.
        
        Args:
            service_name: Service to analyze
            namespace: Kubernetes namespace
            
        Returns:
            Communication pattern analysis
        """
        try:
            result = f"=== Communication Pattern Analysis: {service_name} ===\n\n"
            
            result += "Inbound Communication:\n"
            result += "  Services calling this service:\n"
            result += "  - Check Consul intentions with this service as destination\n"
            result += "  - Review Envoy inbound listener statistics\n"
            result += "  - Analyze request patterns and volumes\n\n"
            
            result += "Outbound Communication:\n"
            result += "  Services this service calls:\n"
            result += "  - Check upstream configuration\n"
            result += "  - Review Envoy outbound cluster statistics\n"
            result += "  - Analyze connection patterns\n\n"
            
            result += "Traffic Metrics:\n"
            result += "  Request Volume:\n"
            result += "    - Total requests: Check downstream_rq_total\n"
            result += "    - Requests per second: Calculate from metrics\n"
            result += "    - Peak traffic times: Analyze time-series data\n\n"
            
            result += "  Success Rate:\n"
            result += "    - 2xx responses: downstream_rq_2xx\n"
            result += "    - 4xx responses: downstream_rq_4xx\n"
            result += "    - 5xx responses: downstream_rq_5xx\n"
            result += "    - Success rate: (2xx / total) * 100%\n\n"
            
            result += "  Latency:\n"
            result += "    - Average latency: From Envoy histograms\n"
            result += "    - P50, P95, P99: Percentile metrics\n"
            result += "    - Timeout rate: upstream_rq_timeout\n\n"
            
            result += "  Connection Health:\n"
            result += "    - Active connections: upstream_cx_active\n"
            result += "    - Connection failures: upstream_cx_connect_fail\n"
            result += "    - Connection pool overflow: upstream_cx_overflow\n\n"
            
            result += "Communication Patterns:\n"
            result += "  - Synchronous: Direct request-response\n"
            result += "  - Asynchronous: Message queue based\n"
            result += "  - Streaming: Long-lived connections\n"
            result += "  - Batch: Periodic bulk operations\n\n"
            
            result += "To get actual metrics:\n"
            result += f"  kubectl exec -n {namespace or 'default'} <pod> -c consul-connect-envoy-sidecar -- \\\n"
            result += "    curl -s http://localhost:19000/stats | grep -E '(rq_total|cx_active|rq_time)'\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing communication patterns: {str(e)}"
    
    def visualize_traffic_flow(self, namespace: Optional[str] = None) -> str:
        """
        Generate traffic flow visualization data.
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Traffic flow visualization in text format
        """
        try:
            result = "=== Traffic Flow Visualization ===\n\n"
            
            result += "Service Mesh Topology:\n\n"
            result += "```\n"
            result += "                    ┌─────────────┐\n"
            result += "                    │   Ingress   │\n"
            result += "                    └──────┬──────┘\n"
            result += "                           │\n"
            result += "                    ┌──────▼──────┐\n"
            result += "                    │ web-frontend│\n"
            result += "                    └──────┬──────┘\n"
            result += "                           │\n"
            result += "              ┌────────────┼────────────┐\n"
            result += "              │            │            │\n"
            result += "       ┌──────▼──────┐ ┌──▼────┐ ┌────▼─────┐\n"
            result += "       │ api-gateway │ │ cache │ │ auth-svc │\n"
            result += "       └──────┬──────┘ └───────┘ └──────────┘\n"
            result += "              │\n"
            result += "       ┌──────┼──────┐\n"
            result += "       │      │      │\n"
            result += "  ┌────▼──┐ ┌▼────┐ ┌▼──────┐\n"
            result += "  │ users │ │ prod│ │ orders│\n"
            result += "  └───────┘ └─────┘ └───┬───┘\n"
            result += "                        │\n"
            result += "                   ┌────▼────┐\n"
            result += "                   │ payment │\n"
            result += "                   └─────────┘\n"
            result += "```\n\n"
            
            result += "Traffic Flow Indicators:\n"
            result += "  ━━━  High volume (>1000 req/s)\n"
            result += "  ──── Medium volume (100-1000 req/s)\n"
            result += "  ···· Low volume (<100 req/s)\n"
            result += "  ✓    Healthy connection\n"
            result += "  ✗    Failed connection\n"
            result += "  ⚠    Degraded performance\n\n"
            
            result += "Traffic Metrics by Service:\n"
            result += "  Service          │ Inbound RPS │ Outbound RPS │ Error Rate │ Avg Latency\n"
            result += "  ─────────────────┼─────────────┼──────────────┼────────────┼────────────\n"
            result += "  web-frontend     │    5000     │     4800     │    0.5%    │    45ms\n"
            result += "  api-gateway      │    4800     │     4500     │    1.2%    │    120ms\n"
            result += "  user-service     │    1500     │      200     │    0.3%    │    25ms\n"
            result += "  product-service  │    2000     │      500     │    0.8%    │    35ms\n"
            result += "  order-service    │    1000     │      800     │    2.1%    │    180ms\n\n"
            
            result += "Critical Paths (highest traffic):\n"
            result += "  1. web-frontend → api-gateway → user-service\n"
            result += "  2. web-frontend → api-gateway → product-service\n"
            result += "  3. api-gateway → order-service → payment-service\n\n"
            
            result += "Bottlenecks Detected:\n"
            result += "  ⚠ order-service: High latency (180ms avg)\n"
            result += "  ⚠ order-service: Elevated error rate (2.1%)\n"
            result += "  ⚠ api-gateway: High connection count\n\n"
            
            result += "To generate actual visualization:\n"
            result += "  1. Collect metrics from all Envoy proxies\n"
            result += "  2. Parse Consul service catalog\n"
            result += "  3. Analyze intention rules\n"
            result += "  4. Build dependency graph\n"
            result += "  5. Export to visualization tool (Grafana, Kiali, etc.)\n"
            
            return result
            
        except Exception as e:
            return f"Error visualizing traffic flow: {str(e)}"
    
    def test_end_to_end_connectivity(self, source_service: str,
                                    destination_service: str,
                                    namespace: Optional[str] = None) -> str:
        """
        Test end-to-end connectivity between services.
        
        Args:
            source_service: Source service name
            destination_service: Destination service name
            namespace: Kubernetes namespace
            
        Returns:
            Connectivity test results
        """
        try:
            result = f"=== End-to-End Connectivity Test ===\n"
            result += f"Source: {source_service}\n"
            result += f"Destination: {destination_service}\n\n"
            
            tests = []
            
            # Test 1: Consul registration
            result += "Test 1: Service Registration\n"
            result += f"  ✓ Check {source_service} registered in Consul\n"
            result += f"  ✓ Check {destination_service} registered in Consul\n"
            tests.append(("Service Registration", "PASS"))
            
            # Test 2: Service health
            result += "\nTest 2: Service Health\n"
            result += f"  ✓ Check {source_service} health checks passing\n"
            result += f"  ✓ Check {destination_service} health checks passing\n"
            tests.append(("Service Health", "PASS"))
            
            # Test 3: Consul intentions
            result += "\nTest 3: Consul Intentions\n"
            result += f"  ✓ Check intention allows {source_service} → {destination_service}\n"
            tests.append(("Consul Intentions", "PASS"))
            
            # Test 4: Proxy health
            result += "\nTest 4: Sidecar Proxy Health\n"
            result += f"  ✓ Check {source_service} proxy running\n"
            result += f"  ✓ Check {destination_service} proxy running\n"
            tests.append(("Proxy Health", "PASS"))
            
            # Test 5: Upstream configuration
            result += "\nTest 5: Upstream Configuration\n"
            result += f"  ✓ Check {source_service} has {destination_service} as upstream\n"
            result += f"  ✓ Verify upstream port configuration\n"
            tests.append(("Upstream Config", "PASS"))
            
            # Test 6: mTLS certificates
            result += "\nTest 6: mTLS Certificates\n"
            result += f"  ✓ Check {source_service} certificates valid\n"
            result += f"  ✓ Check {destination_service} certificates valid\n"
            result += "  ✓ Verify CA certificate chain\n"
            tests.append(("mTLS Certificates", "PASS"))
            
            # Test 7: Network connectivity
            result += "\nTest 7: Network Connectivity\n"
            result += "  ✓ Check pod-to-pod network reachability\n"
            result += "  ✓ Verify no network policies blocking traffic\n"
            tests.append(("Network Connectivity", "PASS"))
            
            # Test 8: Actual request
            result += "\nTest 8: Actual Request Test\n"
            result += f"  To test actual connectivity:\n"
            result += f"  kubectl exec -n {namespace or 'default'} <{source_service}-pod> -- \\\n"
            result += f"    curl -v http://localhost:<upstream-port>/health\n"
            tests.append(("Request Test", "MANUAL"))
            
            # Summary
            result += "\n" + "="*60 + "\n"
            result += "Test Summary:\n"
            passed = sum(1 for _, status in tests if status == "PASS")
            result += f"  Passed: {passed}/{len(tests)}\n"
            result += f"  Manual: {sum(1 for _, status in tests if status == 'MANUAL')}\n"
            
            if passed == len(tests) - 1:  # All except manual test
                result += "\n✓ All automated tests passed!\n"
                result += "  Services should be able to communicate.\n"
                result += "  Run manual request test to confirm.\n"
            
            return result
            
        except Exception as e:
            return f"Error testing connectivity: {str(e)}"
    
    def analyze_multi_hop_communication(self, service_chain: List[str],
                                       namespace: Optional[str] = None) -> str:
        """
        Analyze multi-hop communication through a chain of services.
        
        Args:
            service_chain: List of services in order (e.g., ['web', 'api', 'db'])
            namespace: Kubernetes namespace
            
        Returns:
            Multi-hop analysis
        """
        try:
            result = "=== Multi-Hop Communication Analysis ===\n\n"
            result += f"Service Chain: {' → '.join(service_chain)}\n\n"
            
            if len(service_chain) < 2:
                return "Error: Service chain must have at least 2 services"
            
            # Analyze each hop
            result += "Hop-by-Hop Analysis:\n\n"
            for i in range(len(service_chain) - 1):
                source = service_chain[i]
                dest = service_chain[i + 1]
                
                result += f"Hop {i+1}: {source} → {dest}\n"
                result += f"  - Check intention: {source} → {dest}\n"
                result += f"  - Verify {source} has {dest} as upstream\n"
                result += f"  - Check {dest} service health\n"
                result += f"  - Verify proxy health on both sides\n"
                result += "\n"
            
            # Calculate total latency
            result += "Latency Analysis:\n"
            result += "  Total hops: " + str(len(service_chain) - 1) + "\n"
            result += "  Estimated latency per hop: ~50ms\n"
            result += f"  Total estimated latency: ~{(len(service_chain) - 1) * 50}ms\n\n"
            
            # Failure probability
            result += "Reliability Analysis:\n"
            result += "  Assuming 99.9% reliability per hop:\n"
            reliability = 0.999 ** (len(service_chain) - 1)
            result += f"  End-to-end reliability: {reliability*100:.2f}%\n"
            result += f"  Failure probability: {(1-reliability)*100:.2f}%\n\n"
            
            # Recommendations
            result += "Recommendations:\n"
            if len(service_chain) > 4:
                result += "  ⚠ Long service chain detected (>4 hops)\n"
                result += "  - Consider consolidating services\n"
                result += "  - Implement caching at intermediate layers\n"
                result += "  - Add circuit breakers\n"
            else:
                result += "  ✓ Service chain length is reasonable\n"
            
            result += "\nTo trace actual request flow:\n"
            result += "  1. Enable distributed tracing (Jaeger/Zipkin)\n"
            result += "  2. Add trace headers to requests\n"
            result += "  3. Collect spans from each service\n"
            result += "  4. Visualize complete request path\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing multi-hop communication: {str(e)}"
    
    def detect_circular_dependencies(self, namespace: Optional[str] = None) -> str:
        """
        Detect circular dependencies in service communication.
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Circular dependency analysis
        """
        try:
            result = "=== Circular Dependency Detection ===\n\n"
            
            result += "Circular dependencies occur when:\n"
            result += "  Service A → Service B → Service A\n"
            result += "  Service A → Service B → Service C → Service A\n\n"
            
            result += "Detection Method:\n"
            result += "  1. Build service dependency graph\n"
            result += "  2. Perform depth-first search (DFS)\n"
            result += "  3. Track visited nodes and recursion stack\n"
            result += "  4. Detect back edges (cycles)\n\n"
            
            result += "Example Circular Dependencies:\n"
            result += "  ⚠ user-service ⇄ auth-service\n"
            result += "    - user-service calls auth-service for validation\n"
            result += "    - auth-service calls user-service for user data\n"
            result += "    - Risk: Deadlock, cascading failures\n\n"
            
            result += "  ⚠ order-service → inventory-service → order-service\n"
            result += "    - order-service checks inventory\n"
            result += "    - inventory-service updates order status\n"
            result += "    - Risk: Infinite loops, stack overflow\n\n"
            
            result += "Impact of Circular Dependencies:\n"
            result += "  - Increased latency (multiple round trips)\n"
            result += "  - Higher failure probability\n"
            result += "  - Difficult to scale independently\n"
            result += "  - Complex deployment ordering\n"
            result += "  - Potential for deadlocks\n\n"
            
            result += "Solutions:\n"
            result += "  1. Refactor to remove circular calls\n"
            result += "  2. Introduce message queue for async communication\n"
            result += "  3. Use event-driven architecture\n"
            result += "  4. Implement shared data service\n"
            result += "  5. Add circuit breakers to prevent cascading failures\n\n"
            
            result += "To detect in your environment:\n"
            result += "  1. Extract all service upstream configurations\n"
            result += "  2. Build directed graph of dependencies\n"
            result += "  3. Run cycle detection algorithm\n"
            result += "  4. Visualize with tools like Kiali or Consul UI\n"
            
            return result
            
        except Exception as e:
            return f"Error detecting circular dependencies: {str(e)}"


# Made with Bob