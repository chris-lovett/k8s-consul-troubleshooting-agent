#!/bin/bash
# Consul UI Secure Deployment Documentation Server
# This script sets up and serves the documentation locally

set -e

echo "=================================================="
echo "Consul UI Secure Deployment Documentation"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or later"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    echo "Please install pip3"
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install/upgrade dependencies
echo "📥 Installing/upgrading dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Check if mkdocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "❌ Error: MkDocs installation failed"
    exit 1
fi

echo "✓ MkDocs found: $(mkdocs --version)"
echo ""

# Create necessary directories if they don't exist
echo "📁 Checking documentation structure..."
mkdir -p docs/getting-started
mkdir -p docs/architecture
mkdir -p docs/security
mkdir -p docs/deployment
mkdir -p docs/configuration
mkdir -p docs/operations
mkdir -p docs/reference
mkdir -p docs/appendix
mkdir -p docs/stylesheets
mkdir -p docs/javascripts
echo "✓ Documentation structure verified"
echo ""

# Create placeholder CSS if it doesn't exist
if [ ! -f "docs/stylesheets/extra.css" ]; then
    cat > docs/stylesheets/extra.css << 'EOF'
/* Custom styles for Consul UI Secure Deployment Documentation */

:root {
    --consul-purple: #7B42BC;
    --consul-pink: #C73A63;
}

.md-typeset h1 {
    color: var(--consul-purple);
}

.md-typeset .admonition.success {
    border-left-color: #00ca9e;
}

.md-typeset code {
    background-color: rgba(123, 66, 188, 0.1);
}
EOF
    echo "✓ Created custom CSS"
fi

# Create placeholder JavaScript if it doesn't exist
if [ ! -f "docs/javascripts/extra.js" ]; then
    cat > docs/javascripts/extra.js << 'EOF'
// Custom JavaScript for Consul UI Secure Deployment Documentation

document.addEventListener('DOMContentLoaded', function() {
    console.log('Consul UI Secure Deployment Documentation loaded');
});
EOF
    echo "✓ Created custom JavaScript"
fi

echo ""
echo "=================================================="
echo "🚀 Starting Documentation Server"
echo "=================================================="
echo ""
echo "📖 Documentation will be available at:"
echo "   http://localhost:8000"
echo ""
echo "Features:"
echo "  ✓ Live reload enabled"
echo "  ✓ Full-text search"
echo "  ✓ Dark/light mode toggle"
echo "  ✓ Mobile responsive"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

# Serve documentation
mkdocs serve

# Made with Bob
