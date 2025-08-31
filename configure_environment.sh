#!/bin/bash

# Hero Dashboard Environment Configuration Helper
# This script helps set up environment variables for your specific setup

echo "🔧 Hero Dashboard Environment Configuration"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Copy template
cp .env.example .env

echo "✅ Created .env file from template"
echo ""
echo "📝 Please edit .env file and customize the following variables:"
echo ""
echo "   HERO_DASHBOARD_DIR    - Path to your Hero dashboard directory"
echo "   CHIMERA_BASE          - Path to your Chimera/Frontline project"
echo "   GRAPHITI_BASE         - Path to your Graphiti project"
echo "   GITHUB_USERNAME       - Your GitHub username"
echo "   NEO4J_PASSWORD        - Your Neo4j database password"
echo "   LANGSMITH_API_KEY     - Your LangSmith API key (if using)"
echo ""
echo "🚀 After editing .env, run: ./hero"
echo ""
echo "💡 Tip: You can also set these as system environment variables"
echo "   instead of using the .env file"