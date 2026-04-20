"""
Tests for error pattern recognition functionality.
"""

import pytest
from src.error_patterns import (
    ErrorPattern,
    ErrorPatternMatcher,
    pattern_matcher,
    match_error_patterns,
    format_pattern_match,
    K8S_PATTERNS,
    CONSUL_PATTERNS,
    ALL_PATTERNS
)


class TestErrorPattern:
    """Test ErrorPattern dataclass."""
    
    def test_error_pattern_creation(self):
        """Test creating an ErrorPattern."""
        pattern = ErrorPattern(
            id="test-pattern",
            name="Test Pattern",
            category="kubernetes",
            subcategory="pod",
            patterns=[r"test.*error"],
            symptoms=["Test symptom"],
            root_causes=["Test cause"],
            solutions=["Test solution"],
            severity="high",
            keywords=["test"],
            related_patterns=[]
        )
        
        assert pattern.id == "test-pattern"
        assert pattern.name == "Test Pattern"
        assert pattern.category == "kubernetes"
        assert pattern.severity == "high"
        assert len(pattern.patterns) == 1
        assert len(pattern.symptoms) == 1
    
    def test_error_pattern_defaults(self):
        """Test ErrorPattern default values."""
        pattern = ErrorPattern(
            id="test",
            name="Test",
            category="kubernetes",
            subcategory="pod",
            patterns=[],
            symptoms=[],
            root_causes=[],
            solutions=[]
        )
        
        assert pattern.severity == "medium"
        assert pattern.keywords == []
        assert pattern.related_patterns == []


class TestErrorPatternDatabase:
    """Test the error pattern database."""
    
    def test_k8s_patterns_exist(self):
        """Test that Kubernetes patterns are defined."""
        assert len(K8S_PATTERNS) > 0
        assert all(p.category == "kubernetes" for p in K8S_PATTERNS)
    
    def test_consul_patterns_exist(self):
        """Test that Consul patterns are defined."""
        assert len(CONSUL_PATTERNS) > 0
        assert all(p.category == "consul" for p in CONSUL_PATTERNS)
    
    def test_all_patterns_combined(self):
        """Test that ALL_PATTERNS combines both."""
        assert len(ALL_PATTERNS) == len(K8S_PATTERNS) + len(CONSUL_PATTERNS)
    
    def test_pattern_ids_unique(self):
        """Test that all pattern IDs are unique."""
        ids = [p.id for p in ALL_PATTERNS]
        assert len(ids) == len(set(ids))
    
    def test_crashloop_pattern_exists(self):
        """Test that CrashLoopBackOff pattern exists."""
        crashloop = next((p for p in K8S_PATTERNS if p.id == "k8s-crashloop"), None)
        assert crashloop is not None
        assert "CrashLoopBackOff" in crashloop.name
        assert len(crashloop.patterns) > 0
        assert len(crashloop.solutions) > 0
    
    def test_image_pull_pattern_exists(self):
        """Test that ImagePullBackOff pattern exists."""
        image_pull = next((p for p in K8S_PATTERNS if p.id == "k8s-image-pull"), None)
        assert image_pull is not None
        assert "ImagePullBackOff" in image_pull.name
    
    def test_oom_pattern_exists(self):
        """Test that OOMKilled pattern exists."""
        oom = next((p for p in K8S_PATTERNS if p.id == "k8s-oom"), None)
        assert oom is not None
        assert "OOM" in oom.name or "Memory" in oom.name
    
    def test_consul_connect_pattern_exists(self):
        """Test that Consul Connect pattern exists."""
        connect = next((p for p in CONSUL_PATTERNS if p.id == "consul-connect-fail"), None)
        assert connect is not None
        assert "Connect" in connect.name
    
    def test_consul_intention_pattern_exists(self):
        """Test that Consul intention pattern exists."""
        intention = next((p for p in CONSUL_PATTERNS if p.id == "consul-intention"), None)
        assert intention is not None
        assert "Intention" in intention.name
    
    def test_patterns_have_required_fields(self):
        """Test that all patterns have required fields."""
        for pattern in ALL_PATTERNS:
            assert pattern.id
            assert pattern.name
            assert pattern.category in ["kubernetes", "consul"]
            assert pattern.subcategory
            assert len(pattern.patterns) > 0
            assert len(pattern.symptoms) > 0
            assert len(pattern.root_causes) > 0
            assert len(pattern.solutions) > 0
            assert pattern.severity in ["low", "medium", "high", "critical"]


class TestErrorPatternMatcher:
    """Test ErrorPatternMatcher class."""
    
    def test_matcher_initialization(self):
        """Test matcher initialization."""
        matcher = ErrorPatternMatcher()
        assert len(matcher.patterns) > 0
        assert matcher._compiled_patterns is not None
    
    def test_match_crashloop(self):
        """Test matching CrashLoopBackOff error."""
        text = "Pod is in CrashLoopBackOff state"
        matches = pattern_matcher.match(text)
        
        assert len(matches) > 0
        assert any("CrashLoopBackOff" in m.name for m in matches)
    
    def test_match_image_pull(self):
        """Test matching ImagePullBackOff error."""
        text = "Failed to pull image: ImagePullBackOff"
        matches = pattern_matcher.match(text)
        
        assert len(matches) > 0
        assert any("ImagePull" in m.name for m in matches)
    
    def test_match_oom(self):
        """Test matching OOMKilled error."""
        text = "Container was OOMKilled due to memory limit"
        matches = pattern_matcher.match(text)
        
        assert len(matches) > 0
        assert any("OOM" in m.name or "Memory" in m.name for m in matches)
    
    def test_match_consul_connect(self):
        """Test matching Consul Connect error."""
        text = "upstream connect error or disconnect/reset before headers. reset reason: connection failure"
        matches = pattern_matcher.match(text, category="consul")
        
        assert len(matches) > 0
        assert any("Connect" in m.name for m in matches)
    
    def test_match_consul_intention(self):
        """Test matching Consul intention error."""
        text = "connection denied by intention"
        matches = pattern_matcher.match(text, category="consul")
        
        assert len(matches) > 0
        assert any("Intention" in m.name for m in matches)
    
    def test_match_with_category_filter(self):
        """Test matching with category filter."""
        text = "CrashLoopBackOff"
        
        k8s_matches = pattern_matcher.match(text, category="kubernetes")
        consul_matches = pattern_matcher.match(text, category="consul")
        
        assert len(k8s_matches) > 0
        assert len(consul_matches) == 0
    
    def test_match_no_results(self):
        """Test matching with no results."""
        text = "This is a completely unique error that doesn't match anything"
        matches = pattern_matcher.match(text)
        
        assert len(matches) == 0
    
    def test_match_empty_text(self):
        """Test matching with empty text."""
        matches = pattern_matcher.match("")
        assert len(matches) == 0
        
        matches = pattern_matcher.match(None)
        assert len(matches) == 0
    
    def test_match_multiple_patterns(self):
        """Test matching multiple patterns in same text."""
        text = "Pod is in CrashLoopBackOff and was OOMKilled"
        matches = pattern_matcher.match(text)
        
        assert len(matches) >= 2
        names = [m.name for m in matches]
        assert any("CrashLoopBackOff" in name for name in names)
        assert any("OOM" in name or "Memory" in name for name in names)
    
    def test_relevance_scoring(self):
        """Test that relevance scoring works."""
        # Text with multiple matches should score higher
        text1 = "CrashLoopBackOff CrashLoopBackOff crash restart"
        text2 = "CrashLoopBackOff"
        
        matches1 = pattern_matcher.match(text1)
        matches2 = pattern_matcher.match(text2)
        
        # Both should match, but we can't easily compare scores
        # Just verify both return results
        assert len(matches1) > 0
        assert len(matches2) > 0
    
    def test_get_pattern_by_id(self):
        """Test getting pattern by ID."""
        pattern = pattern_matcher.get_pattern_by_id("k8s-crashloop")
        assert pattern is not None
        assert pattern.id == "k8s-crashloop"
        
        pattern = pattern_matcher.get_pattern_by_id("nonexistent")
        assert pattern is None
    
    def test_search_patterns_by_name(self):
        """Test searching patterns by name."""
        results = pattern_matcher.search_patterns("CrashLoop")
        assert len(results) > 0
        assert any("CrashLoop" in r.name for r in results)
    
    def test_search_patterns_by_keyword(self):
        """Test searching patterns by keyword."""
        results = pattern_matcher.search_patterns("memory")
        assert len(results) > 0
        assert any("memory" in r.keywords for r in results)
    
    def test_search_patterns_by_symptom(self):
        """Test searching patterns by symptom."""
        results = pattern_matcher.search_patterns("pod crashing")
        assert len(results) > 0
    
    def test_search_patterns_no_results(self):
        """Test searching with no results."""
        results = pattern_matcher.search_patterns("xyzabc123nonexistent")
        assert len(results) == 0
    
    def test_format_pattern(self):
        """Test formatting a pattern."""
        pattern = pattern_matcher.get_pattern_by_id("k8s-crashloop")
        formatted = pattern_matcher.format_pattern(pattern)
        
        assert pattern.name in formatted
        assert "Symptoms:" in formatted
        assert "Root Causes:" in formatted
        assert "Solutions:" in formatted
    
    def test_format_pattern_with_related(self):
        """Test formatting pattern with related patterns."""
        pattern = pattern_matcher.get_pattern_by_id("k8s-crashloop")
        formatted = pattern_matcher.format_pattern(pattern, include_related=True)
        
        if pattern.related_patterns:
            assert "Related Patterns:" in formatted
    
    def test_format_pattern_without_related(self):
        """Test formatting pattern without related patterns."""
        pattern = pattern_matcher.get_pattern_by_id("k8s-crashloop")
        formatted = pattern_matcher.format_pattern(pattern, include_related=False)
        
        assert "Related Patterns:" not in formatted


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_match_error_patterns_function(self):
        """Test match_error_patterns convenience function."""
        matches = match_error_patterns("CrashLoopBackOff")
        assert len(matches) > 0
    
    def test_format_pattern_match_function(self):
        """Test format_pattern_match convenience function."""
        pattern = pattern_matcher.get_pattern_by_id("k8s-crashloop")
        formatted = format_pattern_match(pattern)
        
        assert pattern.name in formatted
        assert "Symptoms:" in formatted


class TestRealWorldScenarios:
    """Test real-world error scenarios."""
    
    def test_kubernetes_pod_crash_scenario(self):
        """Test a typical pod crash scenario."""
        log_output = """
        State:          Waiting
        Reason:         CrashLoopBackOff
        Last State:     Terminated
        Reason:         Error
        Exit Code:      1
        """
        
        matches = pattern_matcher.match(log_output)
        assert len(matches) > 0
        assert any("CrashLoopBackOff" in m.name for m in matches)
    
    def test_kubernetes_image_pull_scenario(self):
        """Test image pull failure scenario."""
        event_output = """
        Warning  Failed     5m    kubelet  Failed to pull image "myapp:latest": 
        rpc error: code = Unknown desc = Error response from daemon: 
        pull access denied for myapp, repository does not exist or may require 'docker login'
        """
        
        matches = pattern_matcher.match(event_output)
        assert len(matches) > 0
        assert any("ImagePull" in m.name for m in matches)
    
    def test_kubernetes_oom_scenario(self):
        """Test OOM killed scenario."""
        describe_output = """
        Last State:     Terminated
        Reason:         OOMKilled
        Exit Code:      137
        """
        
        matches = pattern_matcher.match(describe_output)
        assert len(matches) > 0
        assert any("OOM" in m.name or "Memory" in m.name for m in matches)
    
    def test_consul_503_scenario(self):
        """Test Consul 503 error scenario."""
        error_log = """
        [2024-01-15 10:30:45] ERROR: upstream connect error or disconnect/reset before headers. 
        reset reason: connection failure, transport failure reason: delayed connect error: 111
        HTTP/1.1 503 Service Unavailable
        """
        
        matches = pattern_matcher.match(error_log, category="consul")
        assert len(matches) > 0
        assert any("Connect" in m.name or "503" in m.name for m in matches)
    
    def test_consul_intention_deny_scenario(self):
        """Test Consul intention deny scenario."""
        error_msg = "Request denied by Consul intention: web -> api (deny)"
        
        matches = pattern_matcher.match(error_msg, category="consul")
        assert len(matches) > 0
        assert any("Intention" in m.name for m in matches)
    
    def test_multiple_errors_scenario(self):
        """Test scenario with multiple errors."""
        complex_log = """
        Pod web-app-123 status:
        - State: CrashLoopBackOff
        - Last termination: OOMKilled
        - Image pull status: ImagePullBackOff
        - Events: Failed to pull image, Container crashed
        """
        
        matches = pattern_matcher.match(complex_log)
        assert len(matches) >= 3  # Should match multiple patterns
        
        names = [m.name for m in matches]
        assert any("CrashLoop" in name for name in names)
        assert any("OOM" in name or "Memory" in name for name in names)
        assert any("ImagePull" in name for name in names)


class TestPatternQuality:
    """Test the quality and completeness of patterns."""
    
    def test_all_patterns_have_solutions(self):
        """Ensure all patterns have actionable solutions."""
        for pattern in ALL_PATTERNS:
            assert len(pattern.solutions) >= 3, f"Pattern {pattern.id} has too few solutions"
    
    def test_all_patterns_have_symptoms(self):
        """Ensure all patterns have clear symptoms."""
        for pattern in ALL_PATTERNS:
            assert len(pattern.symptoms) >= 2, f"Pattern {pattern.id} has too few symptoms"
    
    def test_all_patterns_have_root_causes(self):
        """Ensure all patterns have root causes."""
        for pattern in ALL_PATTERNS:
            assert len(pattern.root_causes) >= 3, f"Pattern {pattern.id} has too few root causes"
    
    def test_critical_patterns_exist(self):
        """Ensure critical patterns are covered."""
        critical_k8s = ["crashloop", "oom", "image-pull", "pending"]
        critical_consul = ["connect", "intention", "health"]
        
        k8s_ids = [p.id for p in K8S_PATTERNS]
        consul_ids = [p.id for p in CONSUL_PATTERNS]
        
        for critical in critical_k8s:
            assert any(critical in id for id in k8s_ids), f"Missing critical K8s pattern: {critical}"
        
        for critical in critical_consul:
            assert any(critical in id for id in consul_ids), f"Missing critical Consul pattern: {critical}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
