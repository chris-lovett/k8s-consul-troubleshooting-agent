# meshtrbl - AI-Powered Service Mesh Troubleshooter

Intelligent troubleshooting for Kubernetes and HashiCorp Consul service mesh using OpenAI GPT-4.

```bash
# Quick install
pip install ".[all]"

# Run setup wizard
meshtrbl --setup

# Start troubleshooting
meshtrbl
```

## What It Does

meshtrbl is an AI assistant that helps you diagnose and fix issues in Kubernetes clusters and Consul service mesh:

- 🔍 **Analyzes pods, logs, and services** - Automatically investigates failures
- 🚀 **Instant diagnosis** - Recognizes 30+ common error patterns
- 💬 **Natural conversation** - Ask questions in plain English
- ⚡ **Fast responses** - Caches results and routes queries intelligently
- 🔧 **Actionable solutions** - Get step-by-step fixes, not just explanations

## Prerequisites

- **Python 3.11+** (use Homebrew on macOS: `brew install python@3.11`)
- **OpenAI API key** ([Get one here](https://platform.openai.com/api-keys))
- **kubectl** configured for your cluster
- **Consul** (optional, for service mesh features)

## Installation

### 1. Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install meshtrbl
pip install --upgrade pip
pip install ".[all]"
```

### 2. Configure with Setup Wizard (Recommended)

```bash
meshtrbl --setup
```

The wizard will guide you through:
- OpenAI API key configuration
- Kubernetes context selection
- Consul connection (if available)
- Feature preferences

**Or** manually create `.env`:

```bash
cp .env.example .env
# Edit .env and add:
OPENAI_API_KEY=your_key_here
```

### 3. Start Troubleshooting

```bash
# Interactive mode (recommended)
meshtrbl

# Single query
meshtrbl --query "Why is my pod crashing?"

# Specific namespace
meshtrbl --namespace production
```

## Quick Examples

### Example 1: Pod Troubleshooting
```
You: My pod web-app-7d8f9c keeps crashing

Agent: Let me check the pod status and logs...
[Analyzes pod and identifies OOMKilled error]

Your pod is being killed due to memory limits (128Mi). 
Recommendations:
1. Increase memory limit to 256Mi or higher
2. Check for memory leaks in your application
3. Monitor actual memory usage

Would you like me to show you how to update the limits?
```

### Example 2: Service Mesh Issues
```
You: Service "api" cannot connect to "database"

Agent: Checking Consul intentions...
[Finds DENY intention blocking traffic]

Found the issue! A DENY intention is blocking traffic 
from "api" to "database" (created 2 days ago).

To fix: consul intention create -allow api database

Would you like me to check for other connectivity issues?
```

### Example 3: Using Commands
```
You: /help              # Show available commands
You: /examples          # See common scenarios
You: /cache             # View cache statistics
You: /clear             # Clear conversation memory
```

## Key Features

### 🎯 Smart Error Recognition
Instantly recognizes 30+ common issues:
- CrashLoopBackOff, ImagePullBackOff, OOMKilled
- Consul intentions, ACL permissions, mTLS issues
- Proxy failures, service registration problems
- And more...

### ⚡ Fast Performance
- **50-88% faster** for common queries (intent routing)
- **95-99% faster** for repeated queries (caching)
- **2-3x faster** for complex issues (parallel workflows)

### 💬 Natural Interaction
- Remembers conversation context
- Understands follow-up questions
- Provides clear, actionable advice
- Interactive commands for memory and cache management

## Configuration Options

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional - Kubernetes
K8S_NAMESPACE=default

# Optional - Consul
CONSUL_HTTP_ADDR=127.0.0.1:8500
CONSUL_HTTP_TOKEN=<your-token>
CONSUL_HTTP_SSL=true
CONSUL_CACERT=/path/to/ca.pem
```

### Command-Line Options

```bash
meshtrbl --help                    # Show all options
meshtrbl --setup                   # Run configuration wizard
meshtrbl --namespace prod          # Use specific namespace
meshtrbl --consul-host consul.svc  # Custom Consul address
meshtrbl --no-memory               # Disable conversation memory
meshtrbl --no-cache                # Disable caching
meshtrbl --use-workflow            # Use LangGraph workflows
meshtrbl --verbose                 # Show detailed logs
```

## Interactive Commands

While chatting with the agent:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/examples` | Show common troubleshooting scenarios |
| `/clear` | Clear conversation memory |
| `/history` | Show conversation history |
| `/summary` | Show conversation summary |
| `/cache` | Show cache statistics |
| `/clearcache` | Clear session cache |
| `exit` or `quit` | End session |

## Consul Setup (Optional)

If using Consul with ACLs enabled:

```bash
# Create read-only policy for troubleshooting
consul acl policy create \
  -name meshtrbl-reader \
  -rules @examples/consul-agent-troubleshooter-policy.hcl

# Create token
consul acl token create \
  -description "meshtrbl troubleshooting token" \
  -policy-name meshtrbl-reader

# Configure
export CONSUL_HTTP_TOKEN=<token-secret-id>
```

See [examples/consul-agent-troubleshooter-policy.hcl](examples/consul-agent-troubleshooter-policy.hcl) for the policy template.

## Documentation

### Getting Started
- [Quick Start Guide](docs/QUICKSTART.md) - 5-minute setup
- [Installation Guide](docs/INSTALL.md) - Detailed installation
- [Configuration Wizard](docs/OPENAI_API_KEY_SETUP.md) - API key setup

### Features
- [Conversation Memory](docs/MEMORY_FEATURE.md) - Context-aware responses
- [Error Pattern Recognition](docs/ERROR_PATTERN_RECOGNITION.md) - Instant diagnosis
- [Intent Routing](docs/INTENT_ROUTING_FEATURE.md) - Fast-path queries
- [Session Caching](docs/SESSION_CACHE_FEATURE.md) - Lightning-fast repeats
- [Consul Connect Diagnostics](docs/CONSUL_CONNECT_FEATURE.md) - Proxy troubleshooting
- [Service Communication Analysis](docs/SERVICE_COMMUNICATION_FEATURE.md) - Multi-hop tracing
- [LangGraph Workflows](docs/PHASE3_LANGGRAPH_WORKFLOWS.md) - Complex scenarios
- [UX Improvements](docs/PHASE4_UX_IMPROVEMENTS.md) - Enhanced interface

### Advanced
- [Packaging Guide](docs/PACKAGING.md) - Distribution
- [Project Summary](PROJECT_SUMMARY.md) - Complete feature list

## Troubleshooting

### Common Issues

**"No module named 'langchain'"**
```bash
source venv/bin/activate
pip install ".[all]"
```

**"Failed to initialize Kubernetes client"**
```bash
kubectl cluster-info  # Verify cluster access
```

**"OpenAI API key error"**
```bash
# Check your .env file
cat .env | grep OPENAI_API_KEY

# Or run setup wizard
meshtrbl --setup
```

**"Connection refused to Consul"**
```bash
# Verify Consul is accessible
curl http://localhost:8500/v1/status/leader

# Check your CONSUL_HTTP_ADDR format (host:port, no http://)
export CONSUL_HTTP_ADDR=127.0.0.1:8500
```

## Architecture

```
User Query → Intent Classification → Fast Path or Full Agent
                                    ↓
                        Error Pattern Recognition
                                    ↓
                        LangChain ReAct Agent (GPT-4)
                                    ↓
                        Tool Selection & Execution
                                    ↓
                    Kubernetes Tools | Consul Tools
                                    ↓
                        Analysis & Recommendations
```

## Contributing

This is a learning project for LangChain and LangGraph. Contributions welcome:
- Add new troubleshooting tools
- Improve error pattern recognition
- Enhance system prompts
- Add support for other service meshes (Istio, Linkerd)

## License

MIT License - See LICENSE file for details

## Credits

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) - AI agent framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration
- [OpenAI GPT-4](https://openai.com/) - Language model
- [Kubernetes Python Client](https://github.com/kubernetes-client/python) - K8s API
- [python-consul](https://github.com/cablehead/python-consul) - Consul API

---

**Need help?** Check the [documentation](docs/) or open an issue.

**Happy Troubleshooting! 🚀**
