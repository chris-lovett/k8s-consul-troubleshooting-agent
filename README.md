# Consul UI Secure Enterprise Deployment Guide

[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://www.mkdocs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Consul](https://img.shields.io/badge/consul-1.21+-purple.svg)](https://www.consul.io/)
[![OpenShift](https://img.shields.io/badge/openshift-4.19+-red.svg)](https://www.openshift.com/)

## Overview

This repository contains comprehensive, production-ready deployment documentation for the Consul UI with enterprise-grade security controls, specifically designed for platform operators in regulated industries (Financial Services, Healthcare, Government, etc.) where security and compliance are top priorities.

### Key Features

- ✅ **Enterprise Security**: Multi-layered authentication, zero-trust architecture
- ✅ **Compliance Ready**: SOC 2, PCI DSS, GDPR, HIPAA, SOX
- ✅ **Production Tested**: Battle-tested in regulated environments
- ✅ **Comprehensive Documentation**: Step-by-step guides with examples
- ✅ **Interactive Web UI**: Beautiful, searchable documentation site

## Quick Start

### View Documentation Locally

```bash
# 1. Install dependencies
pip install mkdocs-material mkdocs-minify-plugin

# 2. Serve documentation locally
mkdocs serve

# 3. Open in browser
open http://localhost:8000
```

The documentation site will be available at `http://localhost:8000` with live reload enabled.

### Build Static Site

```bash
# Build static HTML site
mkdocs build

# Output will be in site/ directory
# Deploy to any web server
```

## Documentation Structure

```
docs/
├── index.md                          # Home page
├── getting-started/
│   ├── overview.md                   # Getting started overview
│   ├── prerequisites.md              # Prerequisites and requirements
│   └── quickstart.md                 # Quick start guide
├── architecture/
│   ├── overview.md                   # Architecture overview
│   ├── security-model.md             # Security architecture
│   ├── metrics-proxy.md              # Metrics proxy architecture
│   └── network-topology.md           # Network design
├── security/
│   ├── overview.md                   # Security overview
│   ├── authentication.md             # Auth & authz
│   ├── network-security.md           # Network security
│   ├── encryption.md                 # Encryption details
│   ├── audit-compliance.md           # Audit and compliance
│   └── checklist.md                  # Security checklist
├── deployment/
│   ├── overview.md                   # Deployment overview
│   ├── pre-deployment.md             # Pre-deployment setup
│   ├── consul-installation.md        # Consul installation
│   ├── ui-configuration.md           # UI configuration
│   ├── metrics-setup.md              # Metrics setup
│   ├── secure-metrics-gateway.md     # Secure metrics gateway
│   └── post-deployment.md            # Post-deployment tasks
├── configuration/
│   ├── helm-values.md                # Helm values reference
│   ├── acl-policies.md               # ACL policies
│   ├── network-policies.md           # Network policies
│   ├── tls-certificates.md           # TLS configuration
│   └── oidc-integration.md           # OIDC setup
├── operations/
│   ├── monitoring.md                 # Monitoring guide
│   ├── backup-recovery.md            # Backup and recovery
│   ├── upgrades.md                   # Upgrade procedures
│   ├── troubleshooting.md            # Troubleshooting guide
│   └── maintenance.md                # Maintenance tasks
├── reference/
│   ├── api.md                        # API reference
│   ├── cli-commands.md               # CLI commands
│   ├── configuration.md              # Configuration reference
│   └── glossary.md                   # Glossary
└── appendix/
    ├── examples.md                   # Example configurations
    ├── scripts.md                    # Deployment scripts
    ├── faq.md                        # FAQ
    └── resources.md                  # Additional resources
```

## Target Environment

- **Consul Version**: Enterprise 1.21+
- **Platform**: OpenShift 4.19+ (on-premises)
- **Security Level**: Enterprise-grade / Regulated Industries
- **Compliance**: SOC 2, PCI DSS, GDPR, HIPAA, SOX

## Features Covered

### Consul UI Capabilities

- **Service Topology Visualization**: Real-time service mesh topology graph
- **Metrics Dashboards**: Integrated performance monitoring with secure access
- **Service Catalog**: Complete service discovery interface
- **Key/Value Store UI**: Secure KV browsing and editing
- **ACL Management**: Role-based access control interface

### Security Features

- **Multi-layered Authentication**: OIDC/SAML with MFA
- **Zero Trust Architecture**: Defense-in-depth security model
- **Encryption Everywhere**: TLS 1.3 for all communications
- **Comprehensive Audit Logging**: Full compliance trail
- **Network Segmentation**: OpenShift Network Policies
- **Least Privilege Access**: Fine-grained ACL policies

### Metrics Deployment Options

1. **Direct Grafana Integration** (Recommended)
   - Lowest security risk
   - Separate authentication
   - Best compliance posture

2. **Secure Metrics Gateway**
   - Defense-in-depth security
   - Multiple authentication layers
   - Production-ready

3. **Built-in Proxy** (Not Recommended for Production)
   - Security concerns in regulated environments
   - Detailed analysis provided

## Prerequisites

Before deploying, ensure you have:

- OpenShift 4.19+ cluster
- Consul Enterprise 1.21+ license
- Internal PKI/CA infrastructure
- OIDC-compatible Identity Provider
- Cluster-admin access
- Basic knowledge of:
  - OpenShift/Kubernetes
  - Consul architecture
  - TLS/PKI concepts
  - OIDC/OAuth2 flows

## Installation

### Option 1: View Documentation Only

```bash
# Install MkDocs and dependencies
pip install mkdocs-material mkdocs-minify-plugin

# Serve documentation
mkdocs serve
```

### Option 2: Deploy Consul UI

Follow the step-by-step guide in the documentation:

1. [Prerequisites](docs/getting-started/prerequisites.md)
2. [Quick Start](docs/getting-started/quickstart.md)
3. [Deployment Guide](docs/deployment/overview.md)

## Usage

### Viewing Documentation

```bash
# Start local server
mkdocs serve

# Access at http://localhost:8000
# Documentation includes:
# - Interactive navigation
# - Full-text search
# - Code syntax highlighting
# - Mermaid diagrams
# - Dark/light mode toggle
```

### Building for Production

```bash
# Build static site
mkdocs build

# Deploy to web server
# Output in site/ directory
```

### Deploying Consul UI

```bash
# 1. Review configuration
vi docs/helm-values-secure-ui.yaml

# 2. Deploy Consul
helm install consul hashicorp/consul \
  --namespace consul-system \
  --values docs/helm-values-secure-ui.yaml

# 3. Validate deployment
kubectl get pods -n consul-system
```

## Documentation Features

### Interactive Elements

- **Search**: Full-text search across all documentation
- **Navigation**: Tabbed navigation with sections
- **Code Blocks**: Syntax highlighting with copy button
- **Diagrams**: Mermaid diagrams for architecture visualization
- **Admonitions**: Info, warning, and tip callouts
- **Dark Mode**: Toggle between light and dark themes

### Content Organization

- **Getting Started**: Quick start and prerequisites
- **Architecture**: System design and security model
- **Security**: Comprehensive security controls
- **Deployment**: Step-by-step deployment guide
- **Configuration**: Detailed configuration references
- **Operations**: Day-2 operations and maintenance
- **Reference**: API docs and CLI commands
- **Appendix**: Examples, scripts, and resources

## Security Considerations

This deployment implements **defense-in-depth** security:

### Layer 1: Network Security
- Network segmentation with OpenShift Network Policies
- mTLS between all components
- No direct internet exposure

### Layer 2: Authentication
- OIDC/SAML integration with corporate IdP
- Multi-factor authentication (MFA) required
- Short-lived tokens (max 8 hours)

### Layer 3: Authorization
- Role-based access control (RBAC)
- Principle of least privilege
- Fine-grained ACL policies

### Layer 4: Data Protection
- TLS 1.3 encryption in transit
- Encryption at rest for Consul data
- Secrets management via OpenShift Secrets/Vault

### Layer 5: Audit & Monitoring
- Comprehensive audit logging
- Real-time security monitoring
- SIEM integration

## Compliance

This deployment meets requirements for:

- **SOC 2 Type II**: Access controls, audit logging, encryption
- **PCI DSS**: Network segmentation, access logging, encryption
- **GDPR**: Data protection, access controls, audit trails
- **HIPAA**: PHI protection, access controls, audit logging
- **SOX**: Change management, audit trails, access controls

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

### Documentation Issues

For documentation issues, please open an issue in this repository.

### Consul Support

For Consul-specific issues:

- [HashiCorp Discuss](https://discuss.hashicorp.com/c/consul)
- [GitHub Issues](https://github.com/hashicorp/consul/issues)
- [HashiCorp Support](https://support.hashicorp.com)

## License

This documentation is provided under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- HashiCorp for Consul and excellent documentation
- The Consul community for feedback and contributions
- MkDocs Material theme for the beautiful documentation framework

---

**Ready to get started?** Run `mkdocs serve` and open http://localhost:8000 to view the full documentation.
