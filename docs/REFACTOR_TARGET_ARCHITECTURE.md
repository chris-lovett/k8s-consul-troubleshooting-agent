# Refactor Target Architecture

This document defines the target package layout and core interfaces for incremental refactoring.

## Target Folder Structure

```text
src/
  agent.py                              # CLI entrypoint + composition root (thin)
  core/
    __init__.py
    interfaces.py                       # Protocol contracts (router, analyzers, planners)
    router.py                           # QueryRouter + RouteKind
    settings.py                         # AppSettings config merge and defaults
  application/
    __init__.py
    orchestration/
      __init__.py
      query_orchestrator.py             # Orchestrates route -> execution path
      execution_planner.py              # Chooses fast-path/workflow/agent mode
    services/
      __init__.py
      diagnostics_service.py            # Coordinates diagnostics calls
      remediation_service.py            # Composes remediation plans
  domain/
    __init__.py
    models/
      __init__.py
      diagnostics.py                    # Pod/Service/Proxy typed models
      routing.py                        # Route decision model
      remediation.py                    # Remediation models
      communication.py                  # Service graph models
    rules/
      __init__.py
      intent_rules.py                   # Intent scoring + priority policies
      pattern_rules.py                  # Pattern matching policies
  infrastructure/
    __init__.py
    adapters/
      __init__.py
      kubernetes_adapter.py             # Wraps Kubernetes API
      consul_adapter.py                 # Wraps Consul API
      llm_adapter.py                    # Wraps ChatOpenAI
    repositories/
      __init__.py
      cache_repository.py               # Session cache wrapper
      memory_repository.py              # Conversation memory wrapper
  tools/
    ...                                 # Existing tools, gradually migrated to adapters
  workflows/
    ...                                 # Existing workflow, gradually migrated to application layer
```

## Interface Contracts (Target)

### Router

```python
class RouterProtocol(Protocol):
    def route(self, query: str) -> RouteKind: ...
```

### Query Orchestrator

```python
class QueryOrchestratorProtocol(Protocol):
    def run(self, query: str) -> str: ...
```

### Diagnostics

```python
class DiagnosticsServiceProtocol(Protocol):
    def run_k8s(self, query: str) -> DiagnosticsResult: ...
    def run_consul(self, query: str) -> DiagnosticsResult: ...
    def run_proxy(self, query: str) -> DiagnosticsResult: ...
```

### Remediation

```python
class RemediationServiceProtocol(Protocol):
    def build_plan(self, diagnostics: DiagnosticsResult) -> RemediationPlan: ...
```

### Infrastructure Adapters

```python
class KubernetesAdapterProtocol(Protocol):
    def get_pod_status(self, pod_name: str, namespace: str) -> PodStatus: ...

class ConsulAdapterProtocol(Protocol):
    def list_services(self) -> ServiceCatalog: ...
```

## PR Breakdown

1. PR 1 (this change): Introduce `core.settings` and `core.router` and wire existing app to them.
2. PR 2: Introduce typed domain models for service communication and return typed outputs.
3. PR 3: Add application orchestrator service and move routing/execution logic out of `TroubleshootingAgent`.
4. PR 4: Move direct API calls into infrastructure adapters and update tools to depend on adapters.
5. PR 5: Update tests to assert typed contracts first, then output formatting.
