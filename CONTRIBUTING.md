# Contributing to HeroDash

Thank you for your interest in contributing to HeroDash! This document provides guidelines and instructions for contributing to the project.

## Branch Protection and Pull Request Workflow

The `main` branch is protected to ensure code quality and maintain repository integrity. **All changes must go through pull requests** and cannot be pushed directly to `main`.

### Quick Start

1. **Fork or clone** the repository
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and commit them with clear, descriptive messages
4. **Push your branch** to the remote repository:
   ```bash
   git push -u origin feature/your-feature-name
   ```
5. **Open a pull request** against the `main` branch
6. **Wait for review** - at least one approval is required before merging
7. **Address feedback** if requested by reviewers
8. **Merge** once approved

### Branch Protection Rules

The `main` branch has the following protection rules:

- ✅ **Pull requests required** - Direct pushes are blocked
- ✅ **At least 1 approval required** - PRs must be reviewed before merging
- ✅ **Stale reviews dismissed** - New commits invalidate previous approvals
- ✅ **Force pushes blocked** - Repository history is protected
- ✅ **Branch deletion blocked** - The main branch cannot be deleted

For detailed information about branch protection, see [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md).

## Code Style and Standards

### Python Code

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings for modules, classes, and functions
- Keep functions focused and single-purpose
- Comment complex logic, but prefer self-documenting code

### Shell Scripts

- Use `#!/usr/bin/env bash` shebang
- Add `set -euo pipefail` for safer scripts
- Quote variables to prevent word splitting
- Use shellcheck for linting when possible

### Documentation

- Update relevant documentation when changing functionality
- Keep README.md accurate and up-to-date
- Document environment variables and configuration options
- Add inline comments for complex logic

## Testing

Before submitting a pull request:

1. **Validate Python syntax**:
   ```bash
   python3 -m py_compile web_dashboard.py
   ```

2. **Run tests** if available:
   ```bash
   pytest -q tests/
   ```

3. **Validate shell scripts**:
   ```bash
   bash -n launch_web_dashboard.sh
   ```

4. **Test locally** - Run the dashboard and verify your changes work as expected

## Commit Messages

Write clear, descriptive commit messages:

- Use the imperative mood ("Add feature" not "Added feature")
- Start with a capital letter
- Keep the first line under 72 characters
- Add detailed explanation in the body if needed

Good examples:
```
Add Hermes health check endpoint

Add branch protection documentation

Fix Telegram status probe when config is missing
```

## Pull Request Guidelines

When opening a pull request:

1. **Use a descriptive title** that summarizes the change
2. **Fill out the PR description** with:
   - What changed and why
   - How to test the changes
   - Any breaking changes or migration notes
   - Screenshots if relevant (especially for UI changes)
3. **Link related issues** if applicable
4. **Keep PRs focused** - One feature or fix per PR when possible
5. **Respond to feedback** promptly and professionally

## Review Process

Pull request reviews help maintain code quality:

- Reviewers will check for correctness, clarity, and maintainability
- Be open to feedback and willing to make changes
- If you disagree with feedback, discuss respectfully
- Reviews should be completed within a few days

## Getting Help

If you need help or have questions:

- Open an issue for bugs or feature requests
- Check existing documentation in the `docs/` directory
- Review the README.md for setup and usage instructions

## Project Structure

Key files and directories:

```
herodash/
├── web_dashboard.py          # Main dashboard application
├── web_templates/            # HTML templates
├── launch_web_dashboard.sh   # Start/stop script
├── tests/                    # Test files
├── docs/                     # Documentation
│   ├── BRANCH_PROTECTION.md  # Branch protection details
│   └── plans/                # Design documents
└── README.md                 # Main documentation
```

## License

By contributing to HeroDash, you agree that your contributions will be licensed under the same license as the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers and help them learn
- Maintain a professional and collaborative environment

Thank you for contributing to HeroDash! 🚀
