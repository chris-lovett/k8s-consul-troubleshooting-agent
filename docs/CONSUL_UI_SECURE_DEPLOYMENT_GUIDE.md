# Consul UI Secure Enterprise Deployment Guide

## Executive Summary

This guide provides a comprehensive, production-ready deployment plan for the Consul UI with enterprise-grade security controls, specifically designed for financial sector platform operators running Consul 1.21 on OpenShift 4.19 in an on-premises datacenter.

**Target Audience**: Platform operators and security teams in regulated financial environments  
**Environment**: Consul Enterprise 1.21 on OpenShift 4.19 (on-premises)  
**Security Focus**: Enterprise-grade security, compliance, and audit controls

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Security Considerations](#security-considerations)
3. [Prerequisites](#prerequisites)
4. [Deployment Steps](#deployment-steps)
5. [UI Features Configuration](#ui-features-configuration)
6. [Metrics Proxy Security](#metrics-proxy-security)
7. [Access Control & Authentication](#access-control--authentication)
8. [Network Security](#network-security)
9. [Audit & Compliance](#audit--compliance)
10. [Validation & Testing](#validation--testing)
11. [Troubleshooting](#troubleshooting)
12. [References](#references)

---

## Architecture Overview

### Consul UI Components

The Consul UI provides the following enterprise features:

1. **Service Topology Visualization**
   - Real-time service mesh topology graph
   - Service dependency mapping
   - Health status visualization
   - Traffic flow indicators

2. **Metrics Dashboards**
   - Service-level metrics (request rates, latency, errors)
   - Proxy metrics (Envoy sidecar statistics)
   - Custom dashboard URL integration
   - Integration with Prometheus/Grafana

3. **Service Catalog**
   - Service discovery interface
   - Health check monitoring
   - Service intentions management
   - Configuration viewing

4. **Key/Value Store UI**
   - Secure KV browsing and editing
   - ACL-controlled access
   - Namespace isolation (Enterprise)

5. **ACL Management**
   - Token management interface
   - Policy creation and editing
   - Role-based access control

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenShift Cluster                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Consul Namespace                         │ │
│  │                                                              │ │
│  │  ┌──────────────┐      ┌──────────────┐                   │ │
│  │  │ Consul UI    │      │ Consul       │                   │ │
│  │  │ (Service)    │─────▶│ Server       │                   │ │
│  │  │              │      │ (StatefulSet)│                   │ │
│  │  └──────┬───────┘      └──────────────┘                   │ │
│  │         │                                                   │ │
│  │         │ HTTPS (TLS)                                      │ │
│  │         │                                                   │ │
│  │  ┌──────▼───────────────────────────────────────┐         │ │
│  │  │         OpenShift Route (Ingress)            │         │ │
│  │  │  - TLS Termination                           │         │ │
│  │  │  - OAuth/OIDC Integration                    │         │ │
│  │  │  - Rate Limiting                             │         │ │
│  │  └──────────────────────────────────────────────┘         │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Observability Stack (Optional)                 │ │
│  │                                                              │ │
│  │  ┌──────────────┐      ┌──────────────┐                   │ │
│  │  │ Prometheus   │      │ Grafana      │                   │ │
│  │  │              │─────▶│              │                   │ │
│  │  └──────────────┘      └──────────────┘                   │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

External Access:
  Platform Operators ──HTTPS──▶ OpenShift Route ──▶ Consul UI
```

---

## Security Considerations

### Critical Security Requirements for Financial Sector

#### 1. **Authentication & Authorization**

**CRITICAL SECURITY CONTROLS:**

- ✅ **MANDATORY**: Enable ACLs with default-deny policy
- ✅ **MANDATORY**: Integrate with enterprise SSO (OIDC/SAML)
- ✅ **MANDATORY**: Implement role-based access control (RBAC)
- ✅ **MANDATORY**: Use short-lived tokens with automatic rotation
- ✅ **MANDATORY**: Enable audit logging for all UI access

**Implementation Requirements:**
```
- ACL system MUST be enabled before UI deployment
- Default ACL policy MUST be "deny"
- All UI users MUST authenticate via SSO
- Service accounts MUST use Kubernetes service account tokens
- Token TTL MUST NOT exceed 8 hours
```

#### 2. **Network Security**

**CRITICAL SECURITY CONTROLS:**

- ✅ **MANDATORY**: TLS 1.3 for all communications
- ✅ **MANDATORY**: mTLS between Consul components
- ✅ **MANDATORY**: Network policies restricting UI access
- ✅ **MANDATORY**: No direct internet exposure
- ✅ **MANDATORY**: Internal-only routes with VPN/bastion access

**Implementation Requirements:**
```
- TLS certificates from internal PKI/CA
- Certificate rotation every 90 days maximum
- Strong cipher suites only (no weak ciphers)
- Network policies enforcing least-privilege access
- UI accessible only from corporate network
```

#### 3. **Metrics Proxy Security**

**⚠️ CRITICAL WARNING**: The metrics proxy feature has significant security implications.

**From HashiCorp Documentation:**
> "This is intended to simplify setup in test and demo environments. Careful consideration should be given towards using this in production."

**Security Risks:**
1. **Unauthenticated Access**: If ACLs are not enabled, full access to metrics backend is exposed
2. **Privilege Escalation**: Proxy endpoint requires read access to ALL nodes and services
3. **Information Disclosure**: May expose sensitive configuration data
4. **Path Traversal**: Without proper allowlist, unintended API endpoints may be exposed

**PRODUCTION RECOMMENDATIONS:**

For financial sector deployments, we recommend **AGAINST** using the built-in metrics proxy in production. Instead:

**Option A: Direct Integration (RECOMMENDED)**
- Configure dashboard URLs to point directly to Grafana/Prometheus
- Use Grafana's built-in authentication and authorization
- Implement network policies to control access
- No proxy = reduced attack surface

**Option B: Secure Proxy Implementation (If Required)**
- Deploy dedicated, hardened proxy service
- Implement strict path allowlisting
- Add authentication layer (OAuth2 proxy)
- Enable comprehensive audit logging
- Regular security reviews

**Option C: Read-Only Metrics View**
- Use Consul's built-in Prometheus provider
- Configure with minimal ACL permissions
- Implement strict path allowlist
- Monitor for unauthorized access attempts

#### 4. **Data Protection**

**CRITICAL SECURITY CONTROLS:**

- ✅ **MANDATORY**: Encryption at rest for Consul data
- ✅ **MANDATORY**: Encryption in transit (TLS everywhere)
- ✅ **MANDATORY**: Secrets stored in OpenShift Secrets/Vault
- ✅ **MANDATORY**: No sensitive data in logs
- ✅ **MANDATORY**: PII/PCI data segregation

#### 5. **Compliance Requirements**

**Financial Sector Compliance:**

- **SOC 2 Type II**: Audit logging, access controls, encryption
- **PCI DSS**: Network segmentation, access logging, encryption
- **GDPR**: Data protection, access controls, audit trails
- **SOX**: Change management, audit trails, access controls

**Required Audit Capabilities:**
```
- Who accessed the UI (user identity)
- What actions were performed (read/write operations)
- When access occurred (timestamp with timezone)
- Where access originated (source IP, location)
- What data was accessed (resource identifiers)
```

---

## Prerequisites

### Infrastructure Requirements

1. **OpenShift Cluster**
   - OpenShift 4.19 or later
   - Minimum 3 worker nodes
   - StorageClass for persistent volumes
   - Internal container registry configured

2. **Consul Enterprise**
   - Consul Enterprise 1.21 or later
   - Valid enterprise license
   - Consul Helm chart 1.5.0 or later

3. **Certificate Authority**
   - Internal PKI infrastructure
   - Ability to issue TLS certificates
   - Certificate lifecycle management

4. **Identity Provider**
   - OIDC-compatible IdP (Okta, Azure AD, Keycloak, etc.)
   - Service account for Consul integration
   - User groups for RBAC mapping

5. **Observability Stack (Optional)**
   - Prometheus for metrics collection
   - Grafana for visualization
   - Persistent storage for metrics data

### Access Requirements

- OpenShift cluster-admin access (for initial setup)
- Consul ACL management permissions
- Certificate management access
- IdP configuration access

### Knowledge Requirements

- OpenShift/Kubernetes administration
- Consul architecture and operations
- TLS/PKI concepts
- OIDC/OAuth2 authentication flows
- Network security policies

---

## Deployment Steps

See the companion files for detailed implementation:
- [`helm-values-secure-ui.yaml`](./helm-values-secure-ui.yaml) - Helm configuration
- [`acl-policies/`](./acl-policies/) - ACL policy examples
- [`scripts/`](./scripts/) - Deployment automation scripts
- [`METRICS_PROXY_ARCHITECTURE.md`](./METRICS_PROXY_ARCHITECTURE.md) - Detailed metrics architecture

### Quick Start

```bash
# 1. Create namespace
oc new-project consul-system

# 2. Deploy Consul with secure UI
helm install consul hashicorp/consul \
  --namespace consul-system \
  --values helm-values-secure-ui.yaml

# 3. Configure ACLs
./scripts/configure-acls.sh

# 4. Create secure route
oc apply -f openshift-route.yaml

# 5. Validate deployment
./scripts/validate-deployment.sh
```

For complete step-by-step instructions, see the [Detailed Deployment Guide](./DETAILED_DEPLOYMENT_STEPS.md).

---

## References

### Official Documentation

- [Consul UI Configuration](https://developer.hashicorp.com/consul/docs/agent/config/config-files#ui_config)
- [Configuring Dashboard URLs](https://developer.hashicorp.com/consul/docs/observe/telemetry/vm#configuring-dashboard-urls)
- [Proxy Metrics Tutorial](https://developer.hashicorp.com/consul/tutorials/observe-your-network/proxy-metrics)
- [Consul ACL System](https://developer.hashicorp.com/consul/docs/security/acl)
- [Consul on Kubernetes](https://developer.hashicorp.com/consul/docs/k8s)

### Security Best Practices

- [Consul Security Model](https://developer.hashicorp.com/consul/docs/security)
- [Production Deployment Guide](https://developer.hashicorp.com/consul/tutorials/production-deploy)
- [ACL Best Practices](https://developer.hashicorp.com/consul/tutorials/security/access-control-setup-production)

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-28  
**Target Consul Version**: 1.21+  
**Target OpenShift Version**: 4.19+