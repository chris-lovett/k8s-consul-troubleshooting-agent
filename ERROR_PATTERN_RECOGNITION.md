# Error Pattern Recognition Feature

## Overview

The troubleshooting agent now includes **intelligent error pattern recognition** for instant diagnosis of common Kubernetes and Consul issues. This Phase 2 enhancement dramatically speeds up troubleshooting by matching error messages against a comprehensive database of known patterns with pre-defined solutions.

## Key Benefits

1. **⚡ Instant Diagnosis**: Get immediate solutions for common errors without manual investigation
2. **📚 Knowledge Base**: Access to 15+ common Kubernetes and Consul error patterns
3. **🎯 Accurate Matching**: Regex-based pattern matching with relevance scoring
4. **🔗 Related Patterns**: Discover related issues that might be contributing factors
5. **📖 Comprehensive Solutions**: Each pattern includes symptoms, root causes, and step-by-step solutions

## Supported Error Patterns

### Kubernetes Patterns (8)

1. **CrashLoopBackOff** - Container repeatedly crashes and restarts
2. **ImagePullBackOff** - Cannot pull container image from registry
3. **OOMKilled** - Container killed due to out of memory
4. **Pod Stuck in Pending** - Pod cannot be scheduled to a node
5. **PersistentVolume Issues** - Volume mount and storage problems
6. **Network Connectivity Issues** - Service communication failures
7. **Resource Quota/Limit Issues** - Resource constraints and quotas
8. **Readiness Probe Failures** - Health check failures

### Consul Patterns (7)

1. **Consul Connect Communication Failure** - Service mesh connectivity issues
2. **Intention Blocking Traffic** - Service-to-service access denied
3. **Service Health Check Failures** - Unhealthy service instances
4. **Service Registration Issues** - Services not appearing in catalog
5. **ACL Permission Denied** - Authorization and token issues
6. **mTLS Certificate Issues** - TLS handshake and certificate problems
7. **Consul Cluster Issues** - Leader election and quorum problems

## How It Works

### Pattern Matching Process

```
User Query/Error Message
         ↓
Pattern Matcher (Regex)
         ↓
Relevance Scoring
         ↓
Top Matches Returned
         ↓
Formatted Diagnosis + Solutions
```

### Relevance Scoring

The matcher calculates relevance scores based on:
- Number of pattern regex matches
- Keyword matches in the text
- Severity level (critical > high > medium > low)
- Multiple occurrences of error indicators

## Usage

### Interactive Mode

The agent automatically uses pattern recognition when it encounters error messages:

```bash
python -m src.agent
```

Example conversation:
```
You: My pod is in CrashLoopBackOff

Agent: Let me check the error pattern database...

🔍 **CrashLoopBackOff** (HIGH severity)
Category: Kubernetes - Pod

**Symptoms:**
  • Pod status shows CrashLoopBackOff
  • Container repeatedly crashes and restarts
  • Restart count keeps increasing

**Common Root Causes:**
  • Application crashes immediately on startup
  • Missing or incorrect environment variables
  • Configuration file errors

**Solutions:**
  1. Check container logs: kubectl logs <pod-name> --previous
  2. Verify environment variables and ConfigMaps/Secrets
  3. Check resource limits and requests
  ...
```

### Direct Tool Usage

You can also directly use the pattern recognition tools:

#### 1. Match Error Pattern

Match specific error text against patterns:

```
You: Use match_error_pattern with "ImagePullBackOff"

Agent: [Analyzes and returns matching patterns with solutions]
```

#### 2. Search Error Patterns

Search by keywords or symptoms:

```
You: Use search_error_patterns with "memory"

Agent: [Returns all patterns related to memory issues]
```

### Single Query Mode

```bash
python -m src.agent --query "Pod shows OOMKilled error"
```

The agent will automatically match the error pattern and provide solutions.

## Programming Interface

### Using the Pattern Matcher Directly

```python
from src.error_patterns import pattern_matcher, match_error_patterns

# Match error text
error_log = "Pod is in CrashLoopBackOff state"
matches = match_error_patterns(error_log)

for pattern in matches:
    print(f"Pattern: {pattern.name}")
    print(f"Severity: {pattern.severity}")
    print(f"Solutions: {pattern.solutions}")
```

### Search Patterns

```python
from src.error_patterns import pattern_matcher

# Search by keyword
results = pattern_matcher.search_patterns("connection refused")

for pattern in results:
    print(f"Found: {pattern.name} ({pattern.category})")
```

### Get Specific Pattern

```python
from src.error_patterns import pattern_matcher

# Get pattern by ID
pattern = pattern_matcher.get_pattern_by_id("k8s-crashloop")
if pattern:
    print(pattern_matcher.format_pattern(pattern))
```

### Format Pattern for Display

```python
from src.error_patterns import pattern_matcher, format_pattern_match

pattern = pattern_matcher.get_pattern_by_id("k8s-oom")
formatted = format_pattern_match(pattern)
print(formatted)
```

## Pattern Structure

Each error pattern contains:

```python
@dataclass
class ErrorPattern:
    id: str                      # Unique identifier
    name: str                    # Human-readable name
    category: str                # 'kubernetes' or 'consul'
    subcategory: str             # e.g., 'pod', 'network', 'security'
    patterns: List[str]          # Regex patterns to match
    symptoms: List[str]          # Observable symptoms
    root_causes: List[str]       # Common root causes
    solutions: List[str]         # Step-by-step solutions
    severity: str                # 'low', 'medium', 'high', 'critical'
    keywords: List[str]          # Keywords for searching
    related_patterns: List[str]  # Related pattern IDs
```

## Examples

### Example 1: Kubernetes CrashLoopBackOff

**Input:**
```
State:          Waiting
Reason:         CrashLoopBackOff
Last State:     Terminated
```

**Output:**
```
🔍 **CrashLoopBackOff** (HIGH)
Category: Kubernetes - Pod

**Symptoms:**
  • Pod status shows CrashLoopBackOff
  • Container repeatedly crashes and restarts
  • Restart count keeps increasing
  • Pod never reaches Running state

**Common Root Causes:**
  • Application crashes immediately on startup
  • Missing or incorrect environment variables
  • Configuration file errors
  • Dependency services not available
  • Insufficient resources (CPU/memory)

**Solutions:**
  1. Check container logs: kubectl logs <pod-name> --previous
  2. Verify environment variables and ConfigMaps/Secrets
  3. Check resource limits and requests
  4. Ensure all dependencies are available
  5. Review application startup code
  6. Verify container image and tag are correct
  7. Check liveness/readiness probe configuration

**Related Patterns:**
  • OOMKilled (Out of Memory)
  • ImagePullBackOff
```

### Example 2: Consul Connect Failure

**Input:**
```
upstream connect error or disconnect/reset before headers
HTTP/1.1 503 Service Unavailable
```

**Output:**
```
🔍 **Consul Connect Communication Failure** (CRITICAL)
Category: Consul - Connect

**Symptoms:**
  • Service-to-service calls failing
  • 503 errors from Envoy proxy
  • Upstream connection errors
  • Sidecar proxy not ready

**Common Root Causes:**
  • Intention denying traffic
  • Upstream service unhealthy
  • Sidecar proxy not running
  • mTLS certificate issues
  • Service not registered in Consul

**Solutions:**
  1. Check intentions: consul intention list
  2. Verify service health: consul catalog services
  3. Check sidecar proxy status
  4. Verify mTLS certificates are valid
  5. Ensure service is registered
  6. Review upstream configuration
  7. Check Envoy proxy logs

**Related Patterns:**
  • Intention Blocking Traffic
  • Service Health Check Failures
```

### Example 3: Multiple Pattern Match

**Input:**
```
Pod web-app-123 status:
- State: CrashLoopBackOff
- Last termination: OOMKilled
- Image pull status: ImagePullBackOff
```

**Output:**
```
Found 3 matching error pattern(s):

======================================================================
Match #1: CrashLoopBackOff (HIGH severity)
======================================================================
[Full pattern details...]

======================================================================
Match #2: OOMKilled (Out of Memory) (CRITICAL severity)
======================================================================
[Full pattern details...]

======================================================================
Match #3: ImagePullBackOff (HIGH severity)
======================================================================
[Full pattern details...]
```

## Agent Integration

### How the Agent Uses Pattern Recognition

1. **Automatic Detection**: When the agent encounters error messages in logs, status, or events, it automatically checks the pattern database

2. **Priority Tool**: The system prompt instructs the agent to use pattern matching FIRST before other diagnostic tools

3. **Context-Aware**: Pattern matches are combined with live cluster data for comprehensive diagnosis

4. **Follow-up Actions**: After pattern match, the agent may use other tools to verify the diagnosis

### Agent Workflow

```
User Query: "My pod is crashing"
         ↓
Agent: Check error pattern database
         ↓
Pattern Match: CrashLoopBackOff found
         ↓
Agent: Get pod status (verify)
         ↓
Agent: Get pod logs (investigate)
         ↓
Final Answer: Diagnosis + Solutions from pattern + Live data
```

## Best Practices

### When to Use Pattern Recognition

✅ **Use pattern recognition when:**
- You see specific error messages or status conditions
- Pods are in error states (CrashLoopBackOff, ImagePullBackOff, etc.)
- Services are failing health checks
- Connection errors occur
- You want quick solutions for common issues

❌ **Don't rely solely on patterns for:**
- Unique or custom application errors
- Complex multi-service issues
- Performance problems without clear errors
- Configuration-specific issues

### Combining with Other Tools

Pattern recognition works best when combined with live diagnostics:

1. **Start with pattern match** - Get instant solutions for known issues
2. **Verify with live tools** - Confirm the diagnosis with actual cluster data
3. **Apply solutions** - Use the pattern's solutions as a guide
4. **Follow up** - Check related patterns if the issue persists

### Adding Custom Patterns

To add your own patterns, edit `src/error_patterns.py`:

```python
custom_pattern = ErrorPattern(
    id="custom-error",
    name="My Custom Error",
    category="kubernetes",
    subcategory="pod",
    patterns=[r"my custom error regex"],
    symptoms=["Symptom 1", "Symptom 2"],
    root_causes=["Cause 1", "Cause 2"],
    solutions=["Solution 1", "Solution 2"],
    severity="high",
    keywords=["custom", "error"],
    related_patterns=[]
)

# Add to K8S_PATTERNS or CONSUL_PATTERNS list
K8S_PATTERNS.append(custom_pattern)
```

## Performance Considerations

- **Fast Matching**: Regex patterns are pre-compiled for efficient matching
- **Relevance Scoring**: Results are sorted by relevance to show best matches first
- **No External Calls**: Pattern matching is local and doesn't require API calls
- **Memory Efficient**: Pattern database is loaded once at startup

## Testing

Run the comprehensive test suite:

```bash
# Run all pattern recognition tests
pytest test_error_patterns.py -v

# Run specific test class
pytest test_error_patterns.py::TestErrorPatternMatcher -v

# Run with coverage
pytest test_error_patterns.py --cov=src.error_patterns
```

Test coverage includes:
- Pattern database completeness
- Regex matching accuracy
- Relevance scoring
- Search functionality
- Real-world error scenarios
- Edge cases and error handling

## Troubleshooting

### Pattern Not Matching

If a pattern isn't matching your error:

1. **Check the regex**: Patterns use case-insensitive regex matching
2. **Try search**: Use `search_error_patterns` with keywords
3. **Check category**: Ensure you're searching the right category (k8s vs consul)
4. **Add custom pattern**: Create a custom pattern for your specific error

### Too Many Matches

If you get too many pattern matches:

1. **Use category filter**: Specify 'kubernetes' or 'consul'
2. **Be more specific**: Include more context in the error text
3. **Check top matches**: The most relevant patterns are listed first

### Pattern Database Updates

The pattern database is maintained in `src/error_patterns.py`. To update:

1. Edit the pattern definitions
2. Run tests to ensure patterns work correctly
3. Restart the agent to load new patterns

## Future Enhancements

Planned improvements for Phase 3:

- **Machine Learning**: Learn from past troubleshooting sessions
- **Custom Pattern Import**: Load patterns from external files
- **Pattern Statistics**: Track which patterns are most commonly matched
- **Pattern Suggestions**: Suggest new patterns based on unmatched errors
- **Community Patterns**: Share and import patterns from the community
- **Pattern Versioning**: Track pattern changes and improvements

## Related Documentation

- [README.md](README.md) - Main project documentation
- [MEMORY_FEATURE.md](MEMORY_FEATURE.md) - Conversation memory feature
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview and roadmap
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide

---

**Phase 2 Feature** - Error Pattern Recognition ✅ Complete

For questions or to contribute patterns, see the main README.