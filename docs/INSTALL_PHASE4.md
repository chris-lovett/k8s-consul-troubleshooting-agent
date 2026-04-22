# Installing meshtrbl with Phase 4 UX Improvements

## Quick Start

### 1. Install Dependencies

```bash
# Install with all UX features
pip install -r requirements.txt

# Or install from setup.py
pip install -e .
```

### 2. Run Configuration Wizard

```bash
meshtrbl --setup
```

The wizard will guide you through:
- ✅ OpenAI API key configuration (with validation)
- ✅ Kubernetes context selection
- ✅ Consul connection setup
- ✅ Feature toggles (memory, cache, workflows)
- ✅ Advanced settings

Configuration is saved to `~/.meshtrbl/config.yaml`

### 3. Start Using meshtrbl

```bash
# Interactive chat mode
meshtrbl

# Single query mode
meshtrbl --query "why is my pod failing?"

# Get help
meshtrbl --help
```

## New Features in Phase 4.1

### Rich Terminal Output 🎨

- **Color-coded messages:** Success (green), errors (red), warnings (yellow), info (cyan)
- **Formatted tables:** Clean display of pod lists, service info, etc.
- **Syntax highlighting:** YAML and JSON output with colors
- **Markdown rendering:** Rich text formatting in responses
- **Visual status indicators:** ✓ ✗ ⚠ ℹ️ emojis for quick scanning

### Progress Indicators ⏱️

- **Spinner animation:** Shows the agent is working
- **Elapsed time:** See how long operations take
- **Real-time updates:** Know what's happening during long queries

### Better Error Messages 🚨

Errors now include:
- **Clear titles:** "Permission Denied", "Connection Error", etc.
- **Context:** What was happening when the error occurred
- **Actionable suggestions:** Step-by-step troubleshooting tips

Example:
```
❌ Permission Denied
   While processing your query

💡 Try:
   1. Check your kubeconfig: kubectl config view
   2. Verify namespace access: kubectl auth can-i list pods -n production
   3. Contact your cluster admin for access
```

### Configuration Wizard 🎛️

Interactive setup makes configuration easy:
```bash
meshtrbl --setup
```

Features:
- Validates OpenAI API keys before saving
- Auto-detects Kubernetes contexts
- Lists available namespaces
- Saves configuration for future use
- Easy reconfiguration anytime

### Enhanced Help System 🎓

New commands in interactive mode:
- `/help` - Show all available commands with descriptions
- `/examples` - Display common troubleshooting scenarios

Example scenarios include:
- Pod issues (CrashLoopBackOff, high memory, etc.)
- Service communication problems
- Resource constraints
- Network policy issues

### Connection Health Checks 🔍

On startup, meshtrbl checks:
- ✓ Kubernetes cluster connectivity
- ✓ Consul server availability
- ✓ OpenAI API authentication

Skip checks with `--no-health-check` if needed.

## Installation Options

### Option 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/meshtrbl.git
cd meshtrbl

# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python -m src.agent --setup

# Start using
python -m src.agent
```

### Option 2: Development Installation

```bash
# Install in editable mode
pip install -e .

# Run setup
meshtrbl --setup

# Start using
meshtrbl
```

### Option 3: From Package (when published)

```bash
# Install from PyPI (future)
pip install meshtrbl

# Run setup
meshtrbl --setup

# Start using
meshtrbl
```

## Configuration File

The wizard creates `~/.meshtrbl/config.yaml`:

```yaml
openai_api_key: sk-...
model: gpt-4o-mini
kubernetes_namespace: default
consul_host: localhost
consul_port: 8500
enable_memory: true
enable_cache: true
enable_intent_routing: true
enable_workflow: true
cache_ttl: 300
max_iterations: 35
max_execution_time: 300
```

### Manual Configuration

You can also create this file manually or edit it:

```bash
# Create config directory
mkdir -p ~/.meshtrbl

# Edit configuration
nano ~/.meshtrbl/config.yaml
```

## Environment Variables

Configuration can also be set via environment variables (takes precedence over config file):

```bash
export OPENAI_API_KEY="sk-..."
export LLM_MODEL="gpt-4o-mini"
export LLM_REASONING_MODEL="gpt-4o"  # Optional
export K8S_NAMESPACE="default"
export CONSUL_HOST="localhost"
export CONSUL_PORT="8500"
export CONSUL_TOKEN="..."  # Optional
```

## Command-Line Options

All settings can be overridden on the command line:

```bash
meshtrbl \
  --model gpt-4o \
  --namespace production \
  --consul-host consul.example.com \
  --consul-port 8500 \
  --verbose \
  --no-cache
```

### Available Options

```
--setup                 Run configuration wizard
--model MODEL           OpenAI model (default: gpt-4o-mini)
--reasoning-model MODEL Optional stronger model for complex queries
--namespace NS          Kubernetes namespace (default: default)
--consul-host HOST      Consul server host (default: localhost)
--consul-port PORT      Consul server port (default: 8500)
--verbose               Enable verbose logging
--query "..."           Single query mode (non-interactive)
--no-memory             Disable conversation memory
--no-intent-routing     Disable intent classification
--no-cache              Disable session caching
--no-health-check       Skip connection health checks
--cache-ttl SECONDS     Cache TTL (default: 300)
--cache-size SIZE       Max cache entries (default: 100)
--max-iterations N      Max tool calls per query (default: 35)
--max-time SECONDS      Max execution time (default: 300)
```

## Troubleshooting

### Issue: Configuration wizard not working

**Solution:** Install questionary
```bash
pip install questionary
```

### Issue: Colors not showing

**Solution:** Your terminal may not support colors. Try:
```bash
export TERM=xterm-256color
```

Or use a modern terminal emulator (iTerm2, Windows Terminal, etc.)

### Issue: Health checks failing

**Solution:** Skip health checks if they're causing issues:
```bash
meshtrbl --no-health-check
```

Or check your connections manually:
```bash
kubectl cluster-info
curl http://localhost:8500/v1/status/leader
```

### Issue: OpenAI API key not working

**Solution:** Verify your API key:
1. Check at https://platform.openai.com/api-keys
2. Ensure it has sufficient credits
3. Test with a simple API call

### Issue: Permission denied errors

**Solution:** Check Kubernetes permissions:
```bash
kubectl auth can-i list pods -n <namespace>
kubectl auth can-i get services -n <namespace>
```

## Upgrading from Previous Versions

If you're upgrading from an earlier version:

1. **Update dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Run setup wizard:**
   ```bash
   meshtrbl --setup
   ```

3. **Test the new features:**
   ```bash
   meshtrbl
   /help
   /examples
   ```

All existing functionality is preserved - the new features are additions only!

## Next Steps

After installation:

1. **Run the setup wizard** to configure your environment
2. **Try the examples** with `/examples` command
3. **Explore the help** with `/help` command
4. **Start troubleshooting** your Kubernetes and Consul issues!

## Getting Help

- **In-app help:** Type `/help` in interactive mode
- **Examples:** Type `/examples` to see common scenarios
- **Documentation:** Check the docs/ directory
- **Issues:** Report bugs on GitHub

## What's Next?

Phase 4.2 will add:
- Interactive prompts for namespace/pod selection
- Command autocomplete with tab completion
- Streaming LLM responses
- Profile management for multiple environments
- Export capabilities (JSON, YAML, Markdown)

Stay tuned! 🚀