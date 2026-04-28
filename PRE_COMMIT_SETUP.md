# Pre-commit Hooks Setup

This repository uses [pre-commit](https://pre-commit.com/) hooks to automatically enforce code quality standards before commits.

## Quick Start

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## What's Configured

The pre-commit hooks run the following checks:

- **File Quality**: Trailing whitespace, line endings, YAML/JSON/TOML validation, large file detection, merge conflict markers, private key detection
- **Python Quality**: AST validation, builtin literals, docstring checks, debug statement detection, test naming
- **Ruff**: Fast Python linter combining Flake8, pylint, isort, and more
- **ShellCheck**: Shell script validation
- **Bandit**: Security scanning for Python code
- **mypy**: Type checking (configured leniently for existing codebase)

## Configuration Files

- `.pre-commit-config.yaml` - Main hook configuration
- `pyproject.toml` - Python tool settings (Ruff, Bandit, mypy, pytest)

## Benefits

✅ Consistent code quality across all contributors  
✅ Early detection of common issues  
✅ Automated formatting and import sorting  
✅ Security issue detection  
✅ Reduces code review burden  

## Documentation

See [PRE_COMMIT_SETUP.md](./PRE_COMMIT_SETUP.md) for complete documentation including:
- Detailed hook descriptions
- Installation instructions
- Usage examples
- Troubleshooting guide
- Configuration customization

## Bypassing Hooks (Emergency Only)

```bash
git commit --no-verify -m "Emergency fix"
```

**Warning**: Only use in emergencies. Hooks are there to maintain code quality.
