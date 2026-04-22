# Quick Start Guide - 5 Minutes to First Query

Get meshtrbl running in 5 minutes.

## Step 1: Install (2 minutes)

```bash
# Clone/navigate to project
cd meshtrbl

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install
pip install --upgrade pip
pip install ".[all]"
```

## Step 2: Configure (1 minute)

### Option A: Setup Wizard (Easiest)
```bash
meshtrbl --setup
```
Follow the prompts to configure your OpenAI API key and connections.

### Option B: Manual Setup
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Minimum required in `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

## Step 3: Start Troubleshooting (2 minutes)

```bash
# Start interactive mode
meshtrbl
```

### Try These Queries

```
You: List all pods in the default namespace

You: Why is my pod in CrashLoopBackOff?

You: Check if service "api" can connect to "database"

You: Show me the logs for pod web-app-xyz

You: /help
```

## Common Commands

```bash
# Interactive mode (recommended)
meshtrbl

# Single query
meshtrbl --query "check pod status"

# Specific namespace
meshtrbl --namespace production

# Show help
meshtrbl --help
```

## Interactive Commands

While chatting:
- `/help` - Show commands
- `/examples` - See example queries
- `/cache` - View cache stats
- `/clear` - Clear memory
- `exit` - Quit

## Next Steps

- Read the [full README](../README.md) for all features
- Check [Installation Guide](INSTALL.md) for advanced setup
- Review [example scenarios](../examples/troubleshooting_scenarios.md)

## Troubleshooting Setup

**Can't find meshtrbl command?**
```bash
source venv/bin/activate
```

**OpenAI API key error?**
```bash
meshtrbl --setup  # Run wizard again
```

**Kubernetes connection issues?**
```bash
kubectl cluster-info  # Verify access
```

That's it! You're ready to troubleshoot. 🚀