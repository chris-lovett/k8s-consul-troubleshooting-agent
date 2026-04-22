# HashiCorp Validated Design Integration

## Overview

This document describes the integration of HashiCorp's Validated Design best practices for Consul on Kubernetes into the meshtrbl troubleshooting agent.

## Key Best Practices Extracted

### 1. Architecture Patterns

#### Recommended Deployment Architecture
- **6 Consul servers** in cluster (not 3 or 5)
- Distributed across **3 availability zones** (2 servers per AZ)
- **Redundancy zones** enabled via Autopilot
  - 1 voting server per zone
  - 1 non-voting server per zone (for read scalability and failover)
- **Consul servers outside Kubernetes, clients inside** (recommended pattern)
- Consul dataplane (not client agents) for Kubernetes workloads

#### Kubernetes Deployment
- **Separate node groups** for control plane and data plane
- **Taints on server nodes** to prevent workload scheduling
- **Dedicated nodes** for Consul servers (resource-intensive)
- **Private subnets** for control plane deployment
- **Centralized service VPC** with Transit Gateway/VPC Peering

### 2. Configuration Best Practices

#### Server Configuration
```hcl
# Redundancy Zones (CRITICAL)
autopilot {
  redundancy_zone_tag = "zone"
}
node_meta {
  zone = "${consul_server_availability_zone}"
}

# ACLs (MUST be enabled)
acl {
  enabled = true
  default_policy = "deny"
}

# TLS Configuration
tls {
  defaults {
    verify_incoming = false  # For servers
    verify_outgoing = true
    ca_file = "/etc/consul.d/tls/consul-ca.pem"
  }
  https {
    verify_incoming = true
    verify_outgoing = true
  }
  internal_rpc {
    verify_server_hostname = true  # CRITICAL security setting
  }
}

# Performance tuning
performance {
  raft_multiplier = 1
}
limits {
  rpc_max_conns_per_client = 100
  http_max_conns_per_client = 200
}
```

#### Client Configuration
```hcl
# Auto-encrypt for clients
auto_encrypt {
  allow_tls = true
}

# TLS for clients
tls {
  defaults {
    verify_incoming = true  # Different from servers!
    verify_outgoing = true
  }
}
```

### 3. Sizing Guidelines

#### Control Plane on VMs
| Size | Instance Type (AWS) | CPU | Memory | Disk | IOPS |
|------|---------------------|-----|--------|------|------|
| Initial | m5.large | 2 | 8 GB | 100 GB | 3000 |
| Small | m5.xlarge | 4 | 16 GB | 100 GB | 3000 |
| Large | m5.2xlarge | 8 | 32 GB | 200 GB | 7500 |
| Extra-Large | m5.4xlarge | 16 | 64 GB | 200 GB | 7500 |

#### Control Plane on Kubernetes
```yaml
server:
  resources:
    requests:
      memory: "32Gi"
      cpu: "8"
    limits:
      memory: "32Gi"
      cpu: "8"
  storage: 200Gi
```

**Critical**: Monitor for OOM-killed errors on server agents!

### 4. Networking Requirements

#### Required Ports
| Port | Protocol | Source | Destination | Purpose |
|------|----------|--------|-------------|---------|
| 8300 | TCP | All agents | Server agents | RPC |
| 8301 | TCP/UDP | All agents | All agents | Serf LAN (gossip) |
| 8302 | TCP/UDP | Server agents | Server agents | Serf WAN |
| 8500/8501 | TCP | Localhost | Localhost | HTTP/HTTPS API |
| 8502/8503 | TCP | Envoy Proxy | Server agent | gRPC/gRPC-TLS (xDS) |
| 8600 | TCP/UDP | Localhost | Localhost | DNS |
| 21000-21555 | TCP | All agents | Client/Server | Sidecar proxy range |

#### DNS Configuration
- **Route53 Resolver** for AWS (recommended)
- Forward `.consul` domain to port 8600
- Centralize endpoints in Consul VPC
- Share resolver rules via AWS RAM

### 5. Security Best Practices

#### TLS/mTLS
- **Private CA** for internal RPC (not public CA)
- **Dedicated CA** for Consul (don't share with other systems)
- **verify_server_hostname = true** (prevents clients becoming servers)
- **Auto-encrypt** for client certificates
- **Vault integration** for automated certificate management (recommended)

#### Certificate SANs
- Servers: `server.<datacenter>.<domain>` and `<node_name>.server.<datacenter>.<domain>`
- Clients: Unique names (no specific SAN required)

#### ACL Tokens Required
- Bootstrap Token (management)
- Agent Token
- DNS Token
- Snapshot Token
- API Gateway Token
- Terminating Gateway Token
- Mesh Gateway Token
- ESM Token (for external services)

#### Gossip Encryption
- Base64 encoded 32-byte key
- `encrypt_verify_incoming = true`
- `encrypt_verify_outgoing = true`

### 6. Operational Excellence

#### Disaster Recovery
- **Automated snapshots** via snapshot agent
- Store in S3 with replication to different region
- Configure snapshot interval per RPO requirements
- Default: 1 hour interval, retain 30 snapshots

#### Monitoring & Telemetry
- **Prometheus** (recommended)
- Enable telemetry in agent config:
```hcl
telemetry {
  prometheus_retention_time = "480h"
  disable_hostname = true
  metrics_path = "/v1/agent/metrics"
}
```

#### Autopilot Features
- Automated upgrades
- Dead server cleanup (every 200ms)
- Redundancy zones
- Read replicas (non-voting servers)

### 7. Scalability Limits

- **Maximum 5,000 Consul client agents** per datacenter (general rule)
- Can scale to tens of thousands with proper tuning
- Deploy **read replicas** for read-heavy workloads
- Monitor gossip pool size and churn rate

### 8. Common Misconfigurations

#### Critical Issues
1. **Wrong server count**: Using 3 or 5 servers instead of 6
2. **No redundancy zones**: Not configuring autopilot redundancy zones
3. **ACLs disabled**: Running with `default_policy = "allow"`
4. **TLS misconfiguration**: 
   - `verify_server_hostname = false` (security risk)
   - Using public CA for internal RPC
   - Not enabling auto-encrypt for clients
5. **Resource limits**: Not setting proper CPU/memory limits (causes OOM)
6. **Mixed deployment**: Consul servers inside Kubernetes (not recommended)
7. **No taints**: Workloads scheduled on server nodes
8. **Insufficient IOPS**: Using default disk IOPS (< 3000)
9. **Missing ports**: Firewall blocking required ports
10. **No monitoring**: Not enabling telemetry/metrics

#### Performance Issues
1. **raft_multiplier > 1**: Slows down consensus
2. **No connection limits**: Not setting `rpc_max_conns_per_client`
3. **Insufficient resources**: Undersized instances for workload
4. **No read replicas**: All reads hitting voting servers
5. **Gossip pool too large**: > 5000 agents without tuning

## Integration into meshtrbl

### 1. Enhanced Error Patterns

New patterns to detect validated design violations:
- Server count not 6
- Redundancy zones not configured
- ACLs disabled or misconfigured
- TLS verification disabled
- Resource limits not set
- Wrong deployment pattern (servers in K8s)
- Missing required ports
- Insufficient IOPS
- No monitoring/telemetry

### 2. Enhanced System Prompts

Add validated design expertise:
- Recommended architectures
- Configuration best practices
- Sizing guidelines
- Security requirements
- Operational procedures

### 3. New Intent Types

- `validate_design`: Check deployment against validated design
- `check_server_count`: Verify 6-server configuration
- `check_redundancy_zones`: Verify autopilot configuration
- `check_acl_config`: Verify ACL best practices
- `check_tls_config`: Verify TLS/mTLS configuration
- `check_resource_limits`: Verify pod resource limits
- `check_monitoring`: Verify telemetry configuration

### 4. Validation Tools

New tools to check against best practices:
- `validate_consul_architecture`: Check server count, AZ distribution
- `validate_consul_config`: Check configuration against best practices
- `validate_k8s_resources`: Check pod resources, taints, node groups
- `validate_network_config`: Check ports, DNS, load balancers
- `validate_security_config`: Check ACLs, TLS, certificates

## References

- HashiCorp Validated Design: Consul Solution Design Guide (April 2026)
- Consul Enterprise 1.19.x+ent
- Kubernetes 1.27+
- AWS EKS, GCP GKE, Azure AKS

## Next Steps

1. ✅ Extract best practices from validated design
2. ⏳ Create error patterns for common misconfigurations
3. ⏳ Enhance system prompts with validated design knowledge
4. ⏳ Add intent types for design validation
5. ⏳ Create validation tools
6. ⏳ Update documentation
7. ⏳ Test with validation scenarios