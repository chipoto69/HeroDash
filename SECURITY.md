# Security Guide

## Overview
This document outlines the security measures implemented in the Hero Dashboard and how to properly configure sensitive data.

## Critical Security Fixes Applied

### 1. Removed Hardcoded Credentials
- **Fixed**: Hardcoded Neo4j password in `monitors/graphiti_monitor.py`
- **Fixed**: Hardcoded GitHub username in `monitors/github_activity_monitor.py`
- **Fixed**: Extensive hardcoded paths throughout the codebase

### 2. Environment Variable Configuration
All sensitive data is now managed through environment variables:

#### Required Environment Variables
```bash
# GitHub configuration
GITHUB_USERNAME=your_github_username

# Neo4j configuration  
NEO4J_PASSWORD=your_neo4j_password
```

#### Optional Environment Variables
```bash
# Base directories (will use defaults if not set)
HERO_DASHBOARD_DIR=/path/to/your/hero_dashboard
CHIMERA_BASE=/path/to/your/chimera/project
GRAPHITI_BASE=/path/to/your/graphiti/project

# Neo4j additional settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j

# LangSmith configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=hero-command-centre
```

## Setup Instructions

### 1. Create Environment File
```bash
cp .env.example .env
```

### 2. Edit Environment File
Fill in your actual values in the `.env` file:
```bash
nano .env
```

### 3. Load Environment Variables
```bash
# Option 1: Source the file
source .env

# Option 2: Use with commands
export $(cat .env | xargs)
```

## Security Best Practices

### 1. Never Commit Sensitive Data
- The `.env` file is now in `.gitignore`
- All hardcoded credentials have been removed
- Use environment variables for all sensitive data

### 2. Validate Configuration
The application will validate required environment variables on startup and fail gracefully if missing.

### 3. Use Strong Passwords
- Use strong, unique passwords for Neo4j
- Consider using password managers for credential management

### 4. Regular Security Audits
- Regularly review environment variables
- Monitor for any new hardcoded credentials
- Keep dependencies updated

## Files Modified for Security

### Critical Fixes
- `monitors/graphiti_monitor.py` - Removed hardcoded password
- `monitors/github_activity_monitor.py` - Removed hardcoded username
- `config.py` - New centralized configuration system
- `.env.example` - Template for environment variables
- `.gitignore` - Added security-related exclusions

### Path Standardization
All hardcoded paths have been replaced with environment variables:
- `/Users/rudlord/Hero_dashboard/` → `HERO_DASHBOARD_DIR`
- `/Users/rudlord/q3/Frontline` → `CHIMERA_BASE`
- `/Users/rudlord/q3/0_MEMORY/graphiti` → `GRAPHITI_BASE`

## Troubleshooting

### Missing Environment Variables
If you see errors about missing environment variables:
1. Check that `.env` file exists and is properly formatted
2. Ensure all required variables are set
3. Verify the environment variables are loaded in your shell

### Configuration Validation
The application will show clear error messages if required environment variables are missing.

## Reporting Security Issues
If you discover any security vulnerabilities:
1. Do not create public issues
2. Contact the maintainer privately
3. Provide detailed reproduction steps