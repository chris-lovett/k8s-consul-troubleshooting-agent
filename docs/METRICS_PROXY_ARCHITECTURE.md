# Consul UI Metrics Proxy Architecture

## Overview

This document provides detailed architecture diagrams and traffic flow analysis for the Consul UI metrics proxy feature, with a focus on security implications for enterprise deployments.

---

## Architecture Options

### Option A: Direct Grafana Integration (RECOMMENDED for Production)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OpenShift Cluster                            │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Consul Namespace                           │  │
│  │                                                                │  │
│  │  ┌─────────────┐                                              │  │
│  │  │             │  1. User accesses UI                         │  │
│  │  │  Consul UI  │◀─────────────────────────────────┐          │  │
│  │  │             │                                    │          │  │
│  │  └──────┬──────┘                                    │          │  │
│  │         │                                           │          │  │
│  │         │ 2. UI returns dashboard                  │          │  │
│  │         │    URL template                           │          │  │
│  │         │                                           │          │  │
│  │         ▼                                           │          │  │
│  │  ┌─────────────┐                                    │          │  │
│  │  │   Consul    │                                    │          │  │
│  │  │   Server    │                                    │          │  │
│  │  │             │                                    │          │  │
│  │  └─────────────┘                                    │          │  │
│  │                                                      │          │  │
│  └──────────────────────────────────────────────────────┼──────────┘  │
│                                                         │          │
│  ┌──────────────────────────────────────────────────────┼──────────┐  │
│  │              Monitoring Namespace                    │          │  │
│  │                                                       │          │  │
│  │  ┌─────────────┐      ┌─────────────┐              │          │  │
│  │  │             │      │             │              │          │  │
│  │  │ Prometheus  │─────▶│  Grafana    │◀─────────────┘          │  │
│  │  │             │      │             │ 3. Browser redirects    │  │
│  │  │             │      │             │    to Grafana           │  │
│  │  └─────────────┘      └─────────────┘                         │  │
│  │                              │                                  │  │
│  │                              │ 4. Grafana authenticates        │  │
│  │                              │    user (OIDC/LDAP)             │  │
│  │                              │                                  │  │
│  │                              ▼                                  │  │
│  │                       ┌─────────────┐                          │  │
│  │                       │    OIDC     │                          │  │
│  │                       │  Provider   │                          │  │
│  │                       └─────────────┘                          │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

Traffic Flow:
1. User clicks "View Metrics" in Consul UI
2. Consul UI returns dashboard URL: https://grafana.domain.com/d/service?var-service=web
3. Browser redirects to Grafana
4. Grafana authenticates user independently
5. User views metrics in Grafana

Security Benefits:
✅ No proxy = reduced attack surface
✅ Grafana handles authentication/authorization
✅ Separate audit logs for metrics access
✅ Network policies can restrict Grafana access
✅ No elevated Consul permissions required
```

---

### Option B: Built-in Metrics Proxy (NOT RECOMMENDED for Production)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OpenShift Cluster                            │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Consul Namespace                           │  │
│  │                                                                │  │
│  │  ┌─────────────┐                                              │  │
│  │  │             │  1. User accesses UI                         │  │
│  │  │  Consul UI  │◀─────────────────────────────────┐          │  │
│  │  │             │                                    │          │  │
│  │  └──────┬──────┘                                    │          │  │
│  │         │                                           │          │  │
│  │         │ 2. UI makes API call to                  │          │  │
│  │         │    /v1/internal/ui/metrics-proxy         │          │  │
│  │         │                                           │          │  │
│  │         ▼                                           │          │  │
│  │  ┌─────────────┐                                    │          │  │
│  │  │   Consul    │  3. Consul proxies request        │          │  │
│  │  │   Server    │     to Prometheus                  │          │  │
│  │  │             │─────────────────┐                  │          │  │
│  │  │ (Metrics    │                 │                  │          │  │
│  │  │  Proxy)     │                 │                  │          │  │
│  │  └─────────────┘                 │                  │          │  │
│  │         ▲                         │                  │          │  │
│  │         │ 5. Returns metrics      │                  │          │  │
│  │         │    data to UI           │                  │          │  │
│  │         │                         │                  │          │  │
│  └─────────┼─────────────────────────┼──────────────────┼──────────┘  │
│            │                         │                  │          │
│  ┌─────────┼─────────────────────────▼──────────────────┼──────────┐  │
│  │         │      Monitoring Namespace                  │          │  │
│  │         │                                             │          │  │
│  │         │      ┌─────────────┐                       │          │  │
│  │         │      │             │  4. Prometheus        │          │  │
│  │         └──────│ Prometheus  │     returns metrics   │          │  │
│  │                │             │                       │          │  │
│  │                │             │                       │          │  │
│  │                └─────────────┘                       │          │  │
│  │                                                       │          │  │
│  └──────────────────────────────────────────────────────┼──────────┘  │
│                                                          │          │
└──────────────────────────────────────────────────────────┼──────────┘
                                                           │
                                                           │
                                                    ┌──────▼──────┐
                                                    │   Browser   │
                                                    │  (renders   │
                                                    │  metrics)   │
                                                    └─────────────┘

Traffic Flow:
1. User accesses Consul UI
2. UI JavaScript makes API call: GET /v1/internal/ui/metrics-proxy?query=...
3. Consul server proxies request to Prometheus
4. Prometheus returns metrics data
5. Consul returns data to UI
6. Browser renders metrics in UI

Security Risks:
⚠️  Consul token grants access to ALL metrics
⚠️  No separate authentication for metrics
⚠️  Potential path traversal if allowlist not configured
⚠️  Consul audit logs may not capture metrics queries
⚠️  Elevated permissions required (read all services/nodes)
⚠️  Metrics backend exposed through Consul API
```

---

### Option C: Secure Proxy with OAuth2 (If Built-in Proxy Required)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OpenShift Cluster                            │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Consul Namespace                           │  │
│  │                                                                │  │
│  │  ┌─────────────┐                                              │  │
│  │  │             │  1. User accesses UI                         │  │
│  │  │  Consul UI  │◀─────────────────────────────────┐          │  │
│  │  │             │                                    │          │  │
│  │  └──────┬──────┘                                    │          │  │
│  │         │                                           │          │  │
│  │         │ 2. UI makes API call                     │          │  │
│  │         │                                           │          │  │
│  │         ▼                                           │          │  │
│  │  ┌─────────────┐                                    │          │  │
│  │  │   OAuth2    │  3. Validates token               │          │  │
│  │  │   Proxy     │◀────────────────┐                 │          │  │
│  │  │             │                  │                 │          │  │
│  │  └──────┬──────┘                  │                 │          │  │
│  │         │                         │                 │          │  │
│  │         │ 4. Forwards to          │                 │          │  │
│  │         │    Consul if valid      │                 │          │  │
│  │         │                         │                 │          │  │
│  │         ▼                         │                 │          │  │
│  │  ┌─────────────┐                 │                 │          │  │
│  │  │   Consul    │  5. Proxies to  │                 │          │  │
│  │  │   Server    │     Prometheus  │                 │          │  │
│  │  │             │─────────────────┼─────┐           │          │  │
│  │  │ (Metrics    │                 │     │           │          │  │
│  │  │  Proxy)     │                 │     │           │          │  │
│  │  └─────────────┘                 │     │           │          │  │
│  │         ▲                         │     │           │          │  │
│  │         │ 7. Returns metrics      │     │           │          │  │
│  │         │                         │     │           │          │  │
│  └─────────┼─────────────────────────┼─────┼───────────┼──────────┘  │
│            │                         │     │           │          │
│  ┌─────────┼─────────────────────────┼─────▼───────────┼──────────┐  │
│  │         │      Monitoring Namespace│                │          │  │
│  │         │                          │                │          │  │
│  │         │      ┌─────────────┐    │                │          │  │
│  │         │      │             │  6. Returns         │          │  │
│  │         └──────│ Prometheus  │     metrics         │          │  │
│  │                │             │                     │          │  │
│  │                │             │                     │          │  │
│  │                └─────────────┘                     │          │  │
│  │                                                     │          │  │
│  └─────────────────────────────────────────────────────┼──────────┘  │
│                                                        │          │
│  ┌─────────────────────────────────────────────────────┼──────────┐  │
│  │                 Identity Provider                   │          │  │
│  │                                                      │          │  │
│  │                 ┌─────────────┐                     │          │  │
│  │                 │    OIDC     │                     │          │  │
│  │                 │  Provider   │◀────────────────────┘          │  │
│  │                 │             │  Token validation              │  │
│  │                 └─────────────┘                                │  │
│  │                                                                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

Traffic Flow:
1. User accesses Consul UI
2. UI makes API call with OAuth token
3. OAuth2 Proxy validates token with IdP
4. If valid, forwards to Consul metrics proxy
5. Consul proxies to Prometheus (with path allowlist)
6. Prometheus returns metrics
7. Data flows back through OAuth2 Proxy to UI

Security Improvements:
✅ Additional authentication layer
✅ Separate token for metrics access
✅ OAuth2 Proxy audit logging
✅ Path allowlist enforcement
✅ Rate limiting at proxy layer
✅ Token validation before Consul access
```

---

## Security Comparison Matrix

| Feature | Direct Grafana | Built-in Proxy | OAuth2 + Proxy |
|---------|---------------|----------------|----------------|
| **Authentication** | Grafana (OIDC/LDAP) | Consul ACL only | OAuth2 + Consul ACL |
| **Authorization** | Grafana RBAC | Consul ACL | OAuth2 + Consul ACL |
| **Audit Logging** | Grafana logs | Consul audit logs | OAuth2 + Consul logs |
| **Attack Surface** | ✅ Minimal | ⚠️ High | ⚠️ Medium |
| **Complexity** | ✅ Low | ✅ Low | ⚠️ High |
| **Compliance** | ✅ Excellent | ❌ Poor | ⚠️ Good |
| **Maintenance** | ✅ Easy | ✅ Easy | ⚠️ Complex |
| **Production Ready** | ✅ Yes | ❌ No | ⚠️ With caution |

---

## Network Flow Details

### Direct Grafana Integration (Recommended)

**Network Policies Required:**

```yaml
# Allow UI to Consul Server
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: consul-ui-to-server
  namespace: consul-system
spec:
  podSelector:
    matchLabels:
      app: consul
      component: ui
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: consul
          component: server
    ports:
    - protocol: TCP
      port: 8501

---
# No direct connection from Consul to Prometheus needed
# Users access Grafana directly via browser
```

**Firewall Rules:**
- Consul UI → Consul Server: Port 8501 (HTTPS)
- User Browser → Grafana: Port 443 (HTTPS)
- Grafana → Prometheus: Port 9090 (HTTP/internal)

**DNS Requirements:**
- `consul-ui.apps.your-domain.com` → OpenShift Route
- `grafana.your-domain.com` → Grafana Route
- Internal: `consul-server.consul-system.svc.cluster.local`

---

### Built-in Metrics Proxy

**Network Policies Required:**

```yaml
# Allow Consul Server to Prometheus
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: consul-server-to-prometheus
  namespace: consul-system
spec:
  podSelector:
    matchLabels:
      app: consul
      component: server
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: monitoring
      podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 9090
```

**Firewall Rules:**
- Consul UI → Consul Server: Port 8501 (HTTPS)
- Consul Server → Prometheus: Port 9090 (HTTP)
- User Browser → Consul UI: Port 443 (HTTPS)

**Security Concerns:**
- ⚠️ Consul server has network access to Prometheus
- ⚠️ Potential for lateral movement if Consul compromised
- ⚠️ Prometheus exposed to Consul namespace

---

## ACL Requirements

### Direct Grafana Integration

**Minimal Consul ACL Policy:**
```hcl
# UI operators only need read access to Consul
service_prefix "" {
  policy = "read"
}

node_prefix "" {
  policy = "read"
}

# No metrics proxy permissions needed
```

**Grafana Permissions:**
```yaml
# Managed separately in Grafana
# Example: Read-only access to specific dashboards
apiVersion: 1
policies:
  - name: consul-metrics-viewer
    permissions:
      - action: dashboards:read
        scope: folders:consul
```

---

### Built-in Metrics Proxy

**Required Consul ACL Policy:**
```hcl
# ELEVATED PERMISSIONS REQUIRED
service_prefix "" {
  policy = "read"  # Read ALL services
}

node_prefix "" {
  policy = "read"  # Read ALL nodes
}

# Metrics proxy requires broad read access
# This violates least-privilege principle
```

**Security Impact:**
- ⚠️ Single token grants access to all metrics
- ⚠️ No granular control over metrics access
- ⚠️ Difficult to audit who accessed what metrics
- ⚠️ Token compromise = full metrics access

---

## Recommended Implementation

### For Financial Sector / High Security Environments

**Use Direct Grafana Integration:**

1. **Deploy Grafana with Consul dashboards**
   ```bash
   helm install grafana grafana/grafana \
     --namespace monitoring \
     --values grafana-values.yaml
   ```

2. **Configure Consul UI with dashboard URLs**
   ```yaml
   ui:
     dashboardURLTemplates:
       service: "https://grafana.domain.com/d/consul-service?var-service={{Service.Name}}"
   ```

3. **Configure Grafana authentication**
   ```yaml
   grafana:
     auth:
       generic_oauth:
         enabled: true
         client_id: grafana-client
         client_secret: ${OAUTH_SECRET}
         scopes: openid email profile
         auth_url: https://idp.domain.com/oauth2/authorize
         token_url: https://idp.domain.com/oauth2/token
   ```

4. **Set up Grafana RBAC**
   ```yaml
   # Map IdP groups to Grafana roles
   role_attribute_path: contains(groups, 'platform-ops') && 'Admin' || 'Viewer'
   ```

5. **Enable Grafana audit logging**
   ```yaml
   grafana:
     log:
       mode: console file
       level: info
     audit:
       enabled: true
       logBackend: file
   ```

**Benefits:**
- ✅ Separate authentication for metrics
- ✅ Granular RBAC in Grafana
- ✅ Comprehensive audit logging
- ✅ Reduced Consul attack surface
- ✅ Easier compliance demonstration

---

## Migration Path

### From Built-in Proxy to Direct Integration

**Phase 1: Deploy Grafana (Parallel)**
```bash
# Deploy Grafana alongside existing setup
helm install grafana grafana/grafana -n monitoring

# Import Consul dashboards
# Configure data sources
# Test dashboard access
```

**Phase 2: Update Consul UI Configuration**
```yaml
# Update Helm values
ui:
  metrics:
    enabled: false  # Disable proxy
  dashboardURLTemplates:
    service: "https://grafana.domain.com/..."
```

**Phase 3: Remove Proxy Configuration**
```bash
# Remove network policies for proxy
oc delete networkpolicy consul-server-to-prometheus

# Remove elevated ACL permissions
consul acl policy update -name ui-operator -rules @minimal-policy.hcl

# Verify no proxy traffic
```

**Phase 4: Validation**
```bash
# Test UI dashboard links
# Verify Grafana authentication
# Check audit logs
# Validate network policies
```

---

## Troubleshooting

### Direct Grafana Integration Issues

**Dashboard links not working:**
```bash
# Check dashboard URL template
oc get cm consul-ui-config -o yaml | grep dashboardURL

# Verify Grafana accessibility
curl -k https://grafana.domain.com/api/health

# Check browser console for errors
```

**Authentication failures:**
```bash
# Verify Grafana OAuth configuration
kubectl exec -n monitoring grafana-0 -- \
  cat /etc/grafana/grafana.ini | grep -A 10 auth.generic_oauth

# Check IdP logs for authentication attempts
```

---

### Built-in Proxy Issues

**Metrics not loading:**
```bash
# Check Consul logs
oc logs -n consul-system consul-server-0 | grep metrics-proxy

# Verify Prometheus connectivity
oc exec -n consul-system consul-server-0 -- \
  curl -s http://prometheus.monitoring.svc:9090/api/v1/query?query=up

# Check ACL permissions
consul acl token read -self
```

**Path traversal errors:**
```bash
# Verify path allowlist configuration
oc get cm consul-ui-config -o yaml | grep -A 5 pathAllowlist

# Check for unauthorized path access in audit logs
oc logs -n consul-system consul-server-0 | grep "403\|401"
```

---

## Conclusion

For production deployments in financial sector environments:

1. **RECOMMENDED**: Use Direct Grafana Integration
   - Lowest security risk
   - Best compliance posture
   - Easiest to audit
   - Separate authentication/authorization

2. **NOT RECOMMENDED**: Built-in Metrics Proxy
   - High security risk
   - Difficult to audit
   - Elevated permissions required
   - Not suitable for production

3. **IF REQUIRED**: OAuth2 + Proxy
   - Only if direct integration impossible
   - Requires significant additional security controls
   - Complex to maintain
   - Regular security reviews mandatory

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-28  
**Security Classification**: Internal Use Only