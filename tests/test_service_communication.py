"""
Tests for service-to-service communication analysis tools.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.tools.service_communication import (
    ServiceCommunicationAnalyzer,
    ServiceNode,
    CommunicationPath,
    TrafficPattern
)


@pytest.fixture
def mock_consul_tools():
    """Create mock Consul tools."""
    return Mock()


@pytest.fixture
def mock_k8s_tools():
    """Create mock Kubernetes tools."""
    return Mock()


@pytest.fixture
def mock_proxy_tools():
    """Create mock proxy tools."""
    return Mock()


@pytest.fixture
def analyzer(mock_consul_tools, mock_k8s_tools, mock_proxy_tools):
    """Create ServiceCommunicationAnalyzer instance."""
    return ServiceCommunicationAnalyzer(
        mock_consul_tools,
        mock_k8s_tools,
        mock_proxy_tools
    )


class TestServiceDependencyMapping:
    """Tests for build_service_dependency_map method."""
    
    def test_dependency_map_generation(self, analyzer, mock_consul_tools):
        """Test dependency map generation."""
        mock_consul_tools.list_services.return_value = "web, api, database"
        
        result = analyzer.build_service_dependency_map()
        
        assert "Service Dependency Map" in result
        assert "Dependencies" in result
        assert "dependency structure" in result.lower()
    
    def test_dependency_map_with_namespace(self, analyzer):
        """Test dependency map with specific namespace."""
        result = analyzer.build_service_dependency_map(namespace="production")
        
        assert "Service Dependency Map" in result
        assert "kubectl get pods" in result


class TestRequestPathTracing:
    """Tests for trace_request_path method."""
    
    def test_trace_path_between_services(self, analyzer, mock_consul_tools):
        """Test tracing request path between two services."""
        mock_consul_tools.check_intention.return_value = "Traffic is ALLOWED"
        mock_consul_tools.get_service_health.return_value = "Service healthy"
        
        result = analyzer.trace_request_path("web", "api")
        
        assert "Request Path Trace" in result
        assert "web → api" in result
        assert "Check Direct Connection" in result
        assert "Verify Consul Intention" in result
        assert "Check Source Service Proxy" in result
        assert "Check Destination Service Health" in result
    
    def test_trace_path_with_namespace(self, analyzer, mock_consul_tools):
        """Test path tracing with namespace."""
        mock_consul_tools.check_intention.return_value = "Allowed"
        mock_consul_tools.get_service_health.return_value = "Healthy"
        
        result = analyzer.trace_request_path("web", "api", namespace="prod")
        
        assert "Request Path Trace" in result
        assert "Complete Request Flow" in result
    
    def test_trace_path_shows_failure_points(self, analyzer, mock_consul_tools):
        """Test that trace shows potential failure points."""
        mock_consul_tools.check_intention.return_value = "Allowed"
        mock_consul_tools.get_service_health.return_value = "Healthy"
        
        result = analyzer.trace_request_path("web", "api")
        
        assert "Potential Failure Points" in result
        assert "Intention denies traffic" in result
        assert "mTLS certificate issues" in result


class TestCommunicationPatternAnalysis:
    """Tests for analyze_communication_patterns method."""
    
    def test_pattern_analysis(self, analyzer):
        """Test communication pattern analysis."""
        result = analyzer.analyze_communication_patterns("api-service")
        
        assert "Communication Pattern Analysis" in result
        assert "Inbound Communication" in result
        assert "Outbound Communication" in result
        assert "Traffic Metrics" in result
    
    def test_pattern_analysis_includes_metrics(self, analyzer):
        """Test that pattern analysis includes key metrics."""
        result = analyzer.analyze_communication_patterns("api-service")
        
        assert "Request Volume" in result
        assert "Success Rate" in result
        assert "Latency" in result
        assert "Connection Health" in result
    
    def test_pattern_analysis_with_namespace(self, analyzer):
        """Test pattern analysis with namespace."""
        result = analyzer.analyze_communication_patterns("api", namespace="prod")
        
        assert "Communication Pattern Analysis" in result
        assert "kubectl exec" in result


class TestTrafficFlowVisualization:
    """Tests for visualize_traffic_flow method."""
    
    def test_traffic_flow_visualization(self, analyzer):
        """Test traffic flow visualization generation."""
        result = analyzer.visualize_traffic_flow()
        
        assert "Traffic Flow Visualization" in result
        assert "Service Mesh Topology" in result
        assert "Traffic Flow Indicators" in result
    
    def test_visualization_includes_metrics(self, analyzer):
        """Test visualization includes traffic metrics."""
        result = analyzer.visualize_traffic_flow()
        
        assert "Traffic Metrics by Service" in result
        assert "Inbound RPS" in result
        assert "Outbound RPS" in result
        assert "Error Rate" in result
        assert "Avg Latency" in result
    
    def test_visualization_shows_bottlenecks(self, analyzer):
        """Test visualization identifies bottlenecks."""
        result = analyzer.visualize_traffic_flow()
        
        assert "Bottlenecks Detected" in result or "Critical Paths" in result


class TestEndToEndConnectivity:
    """Tests for test_end_to_end_connectivity method."""
    
    def test_connectivity_test(self, analyzer):
        """Test end-to-end connectivity testing."""
        result = analyzer.test_end_to_end_connectivity("web", "api")
        
        assert "End-to-End Connectivity Test" in result
        assert "Source: web" in result
        assert "Destination: api" in result
    
    def test_connectivity_test_steps(self, analyzer):
        """Test that connectivity test includes all steps."""
        result = analyzer.test_end_to_end_connectivity("web", "api")
        
        assert "Service Registration" in result
        assert "Service Health" in result
        assert "Consul Intentions" in result
        assert "Sidecar Proxy Health" in result
        assert "Upstream Configuration" in result
        assert "mTLS Certificates" in result
        assert "Network Connectivity" in result
    
    def test_connectivity_test_summary(self, analyzer):
        """Test connectivity test includes summary."""
        result = analyzer.test_end_to_end_connectivity("web", "api")
        
        assert "Test Summary" in result
        assert "Passed" in result


class TestMultiHopCommunication:
    """Tests for analyze_multi_hop_communication method."""
    
    def test_multi_hop_analysis(self, analyzer):
        """Test multi-hop communication analysis."""
        service_chain = ["web", "api", "database"]
        
        result = analyzer.analyze_multi_hop_communication(service_chain)
        
        assert "Multi-Hop Communication Analysis" in result
        assert "web → api → database" in result
        assert "Hop-by-Hop Analysis" in result
    
    def test_multi_hop_latency_calculation(self, analyzer):
        """Test latency calculation for multi-hop."""
        service_chain = ["web", "api", "db"]
        
        result = analyzer.analyze_multi_hop_communication(service_chain)
        
        assert "Latency Analysis" in result
        assert "Total hops: 2" in result
        assert "estimated latency" in result.lower()
    
    def test_multi_hop_reliability(self, analyzer):
        """Test reliability calculation for multi-hop."""
        service_chain = ["web", "api", "db"]
        
        result = analyzer.analyze_multi_hop_communication(service_chain)
        
        assert "Reliability Analysis" in result
        assert "reliability" in result.lower()
        assert "Failure probability" in result
    
    def test_multi_hop_recommendations(self, analyzer):
        """Test recommendations for long chains."""
        long_chain = ["a", "b", "c", "d", "e", "f"]
        
        result = analyzer.analyze_multi_hop_communication(long_chain)
        
        assert "Recommendations" in result
        assert "Long service chain detected" in result or "reasonable" in result
    
    def test_multi_hop_minimum_services(self, analyzer):
        """Test error for insufficient services."""
        result = analyzer.analyze_multi_hop_communication(["single"])
        
        assert "Error" in result or "at least 2 services" in result


class TestCircularDependencyDetection:
    """Tests for detect_circular_dependencies method."""
    
    def test_circular_dependency_detection(self, analyzer):
        """Test circular dependency detection."""
        result = analyzer.detect_circular_dependencies()
        
        assert "Circular Dependency Detection" in result
        assert "circular dependencies occur when" in result.lower()
    
    def test_circular_dependency_examples(self, analyzer):
        """Test that examples are provided."""
        result = analyzer.detect_circular_dependencies()
        
        assert "Example Circular Dependencies" in result
        assert "user-service" in result or "Service A" in result
    
    def test_circular_dependency_impact(self, analyzer):
        """Test impact analysis is included."""
        result = analyzer.detect_circular_dependencies()
        
        assert "Impact of Circular Dependencies" in result
        assert "latency" in result.lower() or "failure" in result.lower()
    
    def test_circular_dependency_solutions(self, analyzer):
        """Test solutions are provided."""
        result = analyzer.detect_circular_dependencies()
        
        assert "Solutions" in result
        assert "Refactor" in result or "message queue" in result


class TestDataStructures:
    """Tests for data structure classes."""
    
    def test_service_node_creation(self):
        """Test ServiceNode creation."""
        node = ServiceNode(
            name="api-service",
            namespace="default",
            instances=3,
            healthy_instances=3
        )
        
        assert node.name == "api-service"
        assert node.namespace == "default"
        assert node.instances == 3
        assert node.healthy_instances == 3
    
    def test_communication_path_creation(self):
        """Test CommunicationPath creation."""
        path = CommunicationPath(
            source="web",
            destination="api",
            allowed=True,
            intention_exists=True,
            proxy_healthy=True,
            upstream_healthy=True
        )
        
        assert path.source == "web"
        assert path.destination == "api"
        assert path.allowed is True
        assert len(path.issues) == 0
    
    def test_traffic_pattern_creation(self):
        """Test TrafficPattern creation."""
        pattern = TrafficPattern(
            source="web",
            destination="api",
            request_count=1000,
            error_rate=0.5,
            avg_latency_ms=45.0
        )
        
        assert pattern.source == "web"
        assert pattern.destination == "api"
        assert pattern.request_count == 1000
        assert pattern.error_rate == 0.5


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_dependency_map_error_handling(self, analyzer, mock_consul_tools):
        """Test error handling in dependency map."""
        mock_consul_tools.list_services.side_effect = Exception("API error")
        
        result = analyzer.build_service_dependency_map()
        
        assert "Error building dependency map" in result
    
    def test_trace_path_error_handling(self, analyzer, mock_consul_tools):
        """Test error handling in path tracing."""
        mock_consul_tools.check_intention.side_effect = Exception("API error")
        
        result = analyzer.trace_request_path("web", "api")
        
        assert "Error tracing request path" in result
    
    def test_pattern_analysis_error_handling(self, analyzer):
        """Test error handling in pattern analysis."""
        # Force an error by passing invalid data
        result = analyzer.analyze_communication_patterns(None)
        
        # Should handle gracefully
        assert "Error" in result or "Communication Pattern Analysis" in result


class TestNamespaceHandling:
    """Tests for namespace parameter handling."""
    
    def test_default_namespace_used(self, analyzer):
        """Test default namespace is used when not specified."""
        result = analyzer.build_service_dependency_map()
        
        # Should work without error
        assert "Service Dependency Map" in result
    
    def test_custom_namespace_used(self, analyzer):
        """Test custom namespace is used when specified."""
        result = analyzer.build_service_dependency_map(namespace="production")
        
        assert "Service Dependency Map" in result


# Made with Bob