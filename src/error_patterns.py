"""
Error pattern recognition for faster diagnosis.

This module contains a database of common Kubernetes and Consul error patterns
with their symptoms, causes, and solutions.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ErrorPattern:
    """Represents a known error pattern with diagnosis and solution."""
    
    id: str
    name: str
    category: str  # 'kubernetes' or 'consul'
    subcategory: str  # e.g., 'pod', 'service', 'network', 'storage'
    patterns: List[str]  # Regex patterns to match
    symptoms: List[str]
    root_causes: List[str]
    solutions: List[str]
    severity: str = "medium"  # 'low', 'medium', 'high', 'critical'
    keywords: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)


# Kubernetes Error Patterns
K8S_PATTERNS = [
    ErrorPattern(
        id="k8s-crashloop",
        name="CrashLoopBackOff",
        category="kubernetes",
        subcategory="pod",
        patterns=[
            r"CrashLoopBackOff",
            r"Back-off restarting failed container",
            r"container .* is waiting to start: CrashLoopBackOff"
        ],
        symptoms=[
            "Pod status shows CrashLoopBackOff",
            "Container repeatedly crashes and restarts",
            "Restart count keeps increasing",
            "Pod never reaches Running state"
        ],
        root_causes=[
            "Application crashes immediately on startup",
            "Missing or incorrect environment variables",
            "Configuration file errors",
            "Dependency services not available",
            "Insufficient resources (CPU/memory)",
            "Application code bugs",
            "Incorrect command or entrypoint"
        ],
        solutions=[
            "Check container logs: kubectl logs <pod-name> --previous",
            "Verify environment variables and ConfigMaps/Secrets",
            "Check resource limits and requests",
            "Ensure all dependencies are available",
            "Review application startup code",
            "Verify container image and tag are correct",
            "Check liveness/readiness probe configuration"
        ],
        severity="high",
        keywords=["crash", "restart", "backoff", "failed container"],
        related_patterns=["k8s-oom", "k8s-image-pull"]
    ),
    
    ErrorPattern(
        id="k8s-image-pull",
        name="ImagePullBackOff",
        category="kubernetes",
        subcategory="pod",
        patterns=[
            r"ImagePullBackOff",
            r"ErrImagePull",
            r"Failed to pull image",
            r"image pull failed",
            r"manifest unknown",
            r"unauthorized.*registry"
        ],
        symptoms=[
            "Pod stuck in ImagePullBackOff or ErrImagePull",
            "Events show image pull failures",
            "Container never starts"
        ],
        root_causes=[
            "Image does not exist in registry",
            "Incorrect image name or tag",
            "Missing image pull secrets",
            "Registry authentication failure",
            "Network connectivity to registry",
            "Private registry without proper credentials"
        ],
        solutions=[
            "Verify image name and tag are correct",
            "Check if image exists: docker pull <image>",
            "Create and attach imagePullSecrets if using private registry",
            "Verify registry credentials: kubectl get secret <secret-name> -o yaml",
            "Check network connectivity to registry",
            "Ensure service account has access to pull secrets"
        ],
        severity="high",
        keywords=["image", "pull", "registry", "unauthorized"],
        related_patterns=["k8s-network"]
    ),
    
    ErrorPattern(
        id="k8s-oom",
        name="OOMKilled (Out of Memory)",
        category="kubernetes",
        subcategory="pod",
        patterns=[
            r"OOMKilled",
            r"Out of memory",
            r"Memory limit exceeded",
            r"container .* was OOMKilled"
        ],
        symptoms=[
            "Container terminated with OOMKilled",
            "Pod restarts frequently",
            "Last state shows OOMKilled",
            "Memory usage at or near limit"
        ],
        root_causes=[
            "Memory limit set too low",
            "Application memory leak",
            "Unexpected memory usage spike",
            "No memory limits set (node exhaustion)",
            "Inefficient memory usage in application"
        ],
        solutions=[
            "Increase memory limits in pod spec",
            "Analyze application memory usage patterns",
            "Check for memory leaks in application code",
            "Set appropriate memory requests and limits",
            "Use memory profiling tools",
            "Consider horizontal pod autoscaling",
            "Review and optimize application memory usage"
        ],
        severity="critical",
        keywords=["oom", "memory", "killed", "limit exceeded"],
        related_patterns=["k8s-crashloop", "k8s-resource"]
    ),
    
    ErrorPattern(
        id="k8s-pending",
        name="Pod Stuck in Pending",
        category="kubernetes",
        subcategory="pod",
        patterns=[
            r"pod.*Pending",
            r"FailedScheduling",
            r"Insufficient.*cpu",
            r"Insufficient.*memory",
            r"no nodes available",
            r"didn't match pod affinity"
        ],
        symptoms=[
            "Pod remains in Pending state",
            "Events show FailedScheduling",
            "Pod never gets scheduled to a node"
        ],
        root_causes=[
            "Insufficient cluster resources (CPU/memory)",
            "No nodes match pod requirements",
            "Node selector or affinity rules too restrictive",
            "Taints on nodes without matching tolerations",
            "PersistentVolume not available",
            "Resource quotas exceeded"
        ],
        solutions=[
            "Check cluster capacity: kubectl top nodes",
            "Review pod resource requests",
            "Verify node selectors and affinity rules",
            "Check node taints: kubectl describe nodes",
            "Ensure PVs are available and bound",
            "Review namespace resource quotas",
            "Consider adding more nodes or reducing requests"
        ],
        severity="high",
        keywords=["pending", "scheduling", "insufficient", "no nodes"],
        related_patterns=["k8s-resource", "k8s-pv"]
    ),
    
    ErrorPattern(
        id="k8s-pv",
        name="PersistentVolume Issues",
        category="kubernetes",
        subcategory="storage",
        patterns=[
            r"FailedMount",
            r"Unable to mount volumes",
            r"PersistentVolumeClaim.*not found",
            r"volume.*not available",
            r"no persistent volumes available"
        ],
        symptoms=[
            "Pod stuck in ContainerCreating",
            "Events show FailedMount",
            "PVC in Pending state",
            "Volume mount failures"
        ],
        root_causes=[
            "PVC not bound to PV",
            "No PV matches PVC requirements",
            "Storage class not available",
            "Volume already mounted on another node",
            "Insufficient storage capacity",
            "Access mode mismatch"
        ],
        solutions=[
            "Check PVC status: kubectl get pvc",
            "Verify PV availability: kubectl get pv",
            "Ensure storage class exists",
            "Check access modes match (ReadWriteOnce, ReadWriteMany)",
            "Verify storage capacity requirements",
            "Check if volume is already attached elsewhere",
            "Review storage provisioner logs"
        ],
        severity="high",
        keywords=["volume", "mount", "pvc", "pv", "storage"],
        related_patterns=["k8s-pending"]
    ),
    
    ErrorPattern(
        id="k8s-network",
        name="Network Connectivity Issues",
        category="kubernetes",
        subcategory="network",
        patterns=[
            r"connection refused",
            r"no route to host",
            r"timeout.*connect",
            r"dial tcp.*connection refused",
            r"network.*unreachable"
        ],
        symptoms=[
            "Services cannot communicate",
            "Connection timeouts or refused",
            "DNS resolution failures",
            "Intermittent connectivity"
        ],
        root_causes=[
            "Service not running or not ready",
            "Incorrect service selector",
            "Network policy blocking traffic",
            "DNS issues (CoreDNS problems)",
            "Firewall or security group rules",
            "Service port mismatch"
        ],
        solutions=[
            "Verify service endpoints: kubectl get endpoints <service>",
            "Check service selector matches pod labels",
            "Review network policies: kubectl get networkpolicies",
            "Test DNS resolution: nslookup <service>",
            "Verify service and container ports match",
            "Check pod-to-pod connectivity",
            "Review CoreDNS logs if DNS issues"
        ],
        severity="high",
        keywords=["connection", "network", "refused", "timeout", "dns"],
        related_patterns=["k8s-service", "consul-connect"]
    ),
    
    ErrorPattern(
        id="k8s-resource",
        name="Resource Quota/Limit Issues",
        category="kubernetes",
        subcategory="resource",
        patterns=[
            r"exceeded quota",
            r"Forbidden.*quota",
            r"resource quota.*exceeded",
            r"limit.*exceeded"
        ],
        symptoms=[
            "Cannot create new pods",
            "Deployments stuck scaling",
            "Resource creation forbidden"
        ],
        root_causes=[
            "Namespace resource quota exceeded",
            "Too many pods requested",
            "CPU/memory limits exceeded",
            "Storage quota exceeded"
        ],
        solutions=[
            "Check resource quotas: kubectl get resourcequota -n <namespace>",
            "Review current usage: kubectl describe resourcequota",
            "Reduce resource requests or increase quota",
            "Delete unused resources",
            "Review and optimize resource allocation"
        ],
        severity="medium",
        keywords=["quota", "limit", "exceeded", "forbidden"],
        related_patterns=["k8s-pending", "k8s-oom"]
    ),
    
    ErrorPattern(
        id="k8s-readiness",
        name="Readiness Probe Failures",
        category="kubernetes",
        subcategory="pod",
        patterns=[
            r"Readiness probe failed",
            r"Liveness probe failed",
            r"probe.*failed.*timeout",
            r"unhealthy.*probe"
        ],
        symptoms=[
            "Pod running but not ready",
            "Service not routing traffic to pod",
            "Frequent pod restarts (liveness)",
            "Endpoints not including pod"
        ],
        root_causes=[
            "Application not starting fast enough",
            "Probe timeout too short",
            "Incorrect probe configuration",
            "Application actually unhealthy",
            "Probe endpoint not responding"
        ],
        solutions=[
            "Increase initialDelaySeconds for probe",
            "Increase timeout and period settings",
            "Verify probe endpoint is correct",
            "Check application health endpoint",
            "Review application startup time",
            "Test probe endpoint manually: curl <endpoint>"
        ],
        severity="medium",
        keywords=["probe", "readiness", "liveness", "unhealthy"],
        related_patterns=["k8s-crashloop", "k8s-service"]
    ),
]

# Consul Error Patterns
CONSUL_PATTERNS = [
    ErrorPattern(
        id="consul-connect-fail",
        name="Consul Connect Communication Failure",
        category="consul",
        subcategory="connect",
        patterns=[
            r"connection refused.*consul",
            r"upstream connect error",
            r"no healthy upstream",
            r"503.*Service Unavailable",
            r"sidecar.*not ready"
        ],
        symptoms=[
            "Service-to-service calls failing",
            "503 errors from Envoy proxy",
            "Upstream connection errors",
            "Sidecar proxy not ready"
        ],
        root_causes=[
            "Intention denying traffic",
            "Upstream service unhealthy",
            "Sidecar proxy not running",
            "mTLS certificate issues",
            "Service not registered in Consul",
            "Incorrect upstream configuration"
        ],
        solutions=[
            "Check intentions: consul intention list",
            "Verify service health: consul catalog services",
            "Check sidecar proxy status",
            "Verify mTLS certificates are valid",
            "Ensure service is registered",
            "Review upstream configuration in service definition",
            "Check Envoy proxy logs"
        ],
        severity="critical",
        keywords=["connect", "upstream", "sidecar", "503", "proxy"],
        related_patterns=["consul-intention", "consul-health"]
    ),
    
    ErrorPattern(
        id="consul-intention",
        name="Intention Blocking Traffic",
        category="consul",
        subcategory="connect",
        patterns=[
            r"intention.*deny",
            r"permission denied.*intention",
            r"connection denied by intention",
            r"no intention.*allow"
        ],
        symptoms=[
            "Service calls blocked",
            "Permission denied errors",
            "Traffic not flowing between services"
        ],
        root_causes=[
            "No allow intention exists",
            "Deny intention takes precedence",
            "Default deny policy active",
            "Intention misconfigured"
        ],
        solutions=[
            "List intentions: consul intention list",
            "Create allow intention: consul intention create -allow <source> <dest>",
            "Check intention precedence (deny > allow)",
            "Verify service names in intentions match",
            "Review default ACL policy",
            "Use intention check: consul intention check <source> <dest>"
        ],
        severity="high",
        keywords=["intention", "deny", "permission", "blocked"],
        related_patterns=["consul-connect-fail", "consul-acl"]
    ),
    
    ErrorPattern(
        id="consul-health",
        name="Service Health Check Failures",
        category="consul",
        subcategory="health",
        patterns=[
            r"health check.*critical",
            r"health check.*failing",
            r"check.*unhealthy",
            r"service.*critical state"
        ],
        symptoms=[
            "Service marked as unhealthy",
            "Service not receiving traffic",
            "Health checks failing",
            "Service instances in critical state"
        ],
        root_causes=[
            "Application actually unhealthy",
            "Health check endpoint not responding",
            "Health check timeout too short",
            "Network issues preventing checks",
            "Incorrect health check configuration"
        ],
        solutions=[
            "Check service health: consul catalog services -service=<name>",
            "Review health check definition",
            "Test health endpoint manually",
            "Increase health check timeout/interval",
            "Check application logs for errors",
            "Verify network connectivity to health endpoint"
        ],
        severity="high",
        keywords=["health", "check", "critical", "unhealthy", "failing"],
        related_patterns=["consul-connect-fail", "consul-registration"]
    ),
    
    ErrorPattern(
        id="consul-registration",
        name="Service Registration Issues",
        category="consul",
        subcategory="service",
        patterns=[
            r"service.*not registered",
            r"failed to register service",
            r"service.*not found",
            r"no such service"
        ],
        symptoms=[
            "Service not appearing in Consul catalog",
            "Service discovery failing",
            "Cannot find service instances"
        ],
        root_causes=[
            "Service registration failed",
            "Consul agent not running",
            "Registration configuration incorrect",
            "ACL token lacks permissions",
            "Network connectivity to Consul"
        ],
        solutions=[
            "Verify Consul agent is running",
            "Check service registration config",
            "Review Consul agent logs",
            "Verify ACL token permissions",
            "Test connectivity to Consul: consul members",
            "Re-register service manually",
            "Check service definition syntax"
        ],
        severity="critical",
        keywords=["registration", "not found", "not registered", "catalog"],
        related_patterns=["consul-health", "consul-acl"]
    ),
    
    ErrorPattern(
        id="consul-acl",
        name="ACL Permission Denied",
        category="consul",
        subcategory="security",
        patterns=[
            r"ACL.*denied",
            r"permission denied",
            r"ACL not found",
            r"invalid ACL token",
            r"token.*insufficient"
        ],
        symptoms=[
            "Operations failing with permission denied",
            "Cannot read/write to Consul",
            "Token validation failures"
        ],
        root_causes=[
            "Missing or invalid ACL token",
            "Token lacks required permissions",
            "ACL policy too restrictive",
            "Token expired or revoked"
        ],
        solutions=[
            "Verify ACL token is set: echo $CONSUL_HTTP_TOKEN",
            "Check token permissions: consul acl token read -id=<token>",
            "Create token with appropriate policy",
            "Review ACL policies: consul acl policy list",
            "Ensure token has required permissions for operation",
            "Use bootstrap token for initial setup"
        ],
        severity="high",
        keywords=["acl", "permission", "denied", "token", "unauthorized"],
        related_patterns=["consul-registration", "consul-intention"]
    ),
    
    ErrorPattern(
        id="consul-mtls",
        name="mTLS Certificate Issues",
        category="consul",
        subcategory="security",
        patterns=[
            r"certificate.*invalid",
            r"certificate.*expired",
            r"TLS.*handshake failed",
            r"x509.*certificate",
            r"certificate verify failed"
        ],
        symptoms=[
            "TLS handshake failures",
            "Certificate validation errors",
            "Secure connections failing"
        ],
        root_causes=[
            "Certificate expired",
            "Certificate not trusted",
            "Certificate name mismatch",
            "CA certificate issues",
            "Clock skew between services"
        ],
        solutions=[
            "Check certificate expiry: consul tls cert inspect",
            "Verify CA certificate is valid",
            "Ensure certificate names match service names",
            "Check system time on all nodes",
            "Rotate certificates if expired",
            "Review Consul Connect CA configuration"
        ],
        severity="critical",
        keywords=["mtls", "certificate", "tls", "x509", "handshake"],
        related_patterns=["consul-connect-fail"]
    ),
    
    ErrorPattern(
        id="consul-cluster",
        name="Consul Cluster Issues",
        category="consul",
        subcategory="cluster",
        patterns=[
            r"no leader",
            r"leader election",
            r"raft.*error",
            r"quorum.*lost",
            r"cluster.*unhealthy"
        ],
        symptoms=[
            "No cluster leader",
            "Cluster operations failing",
            "Raft errors in logs",
            "Quorum lost"
        ],
        root_causes=[
            "Network partition",
            "Insufficient servers for quorum",
            "Server failures",
            "Clock skew between servers",
            "Disk I/O issues"
        ],
        solutions=[
            "Check cluster members: consul members",
            "Verify server count meets quorum (n/2 + 1)",
            "Check network connectivity between servers",
            "Review Consul server logs",
            "Verify system clocks are synchronized",
            "Check disk space and I/O performance",
            "Restart failed servers if needed"
        ],
        severity="critical",
        keywords=["leader", "quorum", "raft", "cluster", "election"],
        related_patterns=[]
    ),
]

# Combined pattern database
ALL_PATTERNS = K8S_PATTERNS + CONSUL_PATTERNS


class ErrorPatternMatcher:
    """Matches error messages and logs against known patterns."""
    
    def __init__(self):
        self.patterns = ALL_PATTERNS
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, ErrorPattern]]]:
        """Compile regex patterns for efficient matching."""
        compiled = {}
        for pattern in self.patterns:
            for regex in pattern.patterns:
                compiled_regex = re.compile(regex, re.IGNORECASE)
                if pattern.category not in compiled:
                    compiled[pattern.category] = []
                compiled[pattern.category].append((compiled_regex, pattern))
        return compiled
    
    def match(self, text: str, category: Optional[str] = None) -> List[ErrorPattern]:
        """
        Match text against error patterns.
        
        Args:
            text: Text to match (logs, error messages, status output)
            category: Optional category filter ('kubernetes' or 'consul')
        
        Returns:
            List of matching ErrorPattern objects, sorted by relevance
        """
        if not text:
            return []
        
        matches = []
        categories = [category] if category else ['kubernetes', 'consul']
        
        for cat in categories:
            if cat not in self._compiled_patterns:
                continue
            
            for regex, pattern in self._compiled_patterns[cat]:
                if regex.search(text):
                    # Calculate relevance score
                    score = self._calculate_relevance(text, pattern)
                    matches.append((score, pattern))
        
        # Remove duplicates and sort by score
        seen = set()
        unique_matches = []
        for score, pattern in sorted(matches, key=lambda x: x[0], reverse=True):
            if pattern.id not in seen:
                seen.add(pattern.id)
                unique_matches.append(pattern)
        
        return unique_matches
    
    def _calculate_relevance(self, text: str, pattern: ErrorPattern) -> float:
        """Calculate relevance score for a pattern match."""
        score = 1.0
        
        # Boost score for multiple pattern matches
        text_lower = text.lower()
        pattern_matches = sum(1 for p in pattern.patterns if re.search(p, text, re.IGNORECASE))
        score += pattern_matches * 0.5
        
        # Boost score for keyword matches
        keyword_matches = sum(1 for kw in pattern.keywords if kw in text_lower)
        score += keyword_matches * 0.3
        
        # Boost score for severity
        severity_boost = {
            'critical': 1.0,
            'high': 0.7,
            'medium': 0.4,
            'low': 0.2
        }
        score += severity_boost.get(pattern.severity, 0)
        
        return score
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[ErrorPattern]:
        """Get a specific pattern by ID."""
        for pattern in self.patterns:
            if pattern.id == pattern_id:
                return pattern
        return None
    
    def search_patterns(self, query: str) -> List[ErrorPattern]:
        """
        Search patterns by name, keywords, or symptoms.
        
        Args:
            query: Search query
        
        Returns:
            List of matching patterns
        """
        query_lower = query.lower()
        matches = []
        
        for pattern in self.patterns:
            # Check name
            if query_lower in pattern.name.lower():
                matches.append((3.0, pattern))
                continue
            
            # Check keywords
            if any(query_lower in kw for kw in pattern.keywords):
                matches.append((2.0, pattern))
                continue
            
            # Check symptoms
            if any(query_lower in symptom.lower() for symptom in pattern.symptoms):
                matches.append((1.5, pattern))
                continue
            
            # Check root causes
            if any(query_lower in cause.lower() for cause in pattern.root_causes):
                matches.append((1.0, pattern))
                continue
        
        return [p for _, p in sorted(matches, key=lambda x: x[0], reverse=True)]
    
    def format_pattern(self, pattern: ErrorPattern, include_related: bool = True) -> str:
        """
        Format a pattern for display.
        
        Args:
            pattern: ErrorPattern to format
            include_related: Include related patterns
        
        Returns:
            Formatted string
        """
        output = []
        output.append(f"🔍 **{pattern.name}** ({pattern.severity.upper()})")
        output.append(f"Category: {pattern.category.title()} - {pattern.subcategory.title()}")
        output.append("")
        
        output.append("**Symptoms:**")
        for symptom in pattern.symptoms:
            output.append(f"  • {symptom}")
        output.append("")
        
        output.append("**Common Root Causes:**")
        for cause in pattern.root_causes:
            output.append(f"  • {cause}")
        output.append("")
        
        output.append("**Solutions:**")
        for i, solution in enumerate(pattern.solutions, 1):
            output.append(f"  {i}. {solution}")
        
        if include_related and pattern.related_patterns:
            output.append("")
            output.append("**Related Patterns:**")
            for related_id in pattern.related_patterns:
                related = self.get_pattern_by_id(related_id)
                if related:
                    output.append(f"  • {related.name}")
        
        return "\n".join(output)


# Global matcher instance
pattern_matcher = ErrorPatternMatcher()


def match_error_patterns(text: str, category: Optional[str] = None) -> List[ErrorPattern]:
    """
    Convenience function to match error patterns.
    
    Args:
        text: Text to match
        category: Optional category filter
    
    Returns:
        List of matching patterns
    """
    return pattern_matcher.match(text, category)


def format_pattern_match(pattern: ErrorPattern) -> str:
    """
    Convenience function to format a pattern.
    
    Args:
        pattern: Pattern to format
    
    Returns:
        Formatted string
    """
    return pattern_matcher.format_pattern(pattern)


# Made with Bob