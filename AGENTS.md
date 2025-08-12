# Repository Guidelines

## Project Structure & Module Organization
- Root scripts: `hero_core_optimized_fixed.sh` (main dashboard), `launch_hero_optimized_fixed.sh` (launcher), `setup_optimized_fixed.sh` (one-time setup).
- Monitors: `monitors/` contains Python helpers (e.g., `claude_usage_monitor_optimized.py`, `github_activity_monitor_optimized.py`).
- Docs: `docs/` plus top-level references like `README.md`, `README_OPTIMIZED.md`, `FINAL_STRUCTURE.md`.
- Cache/logs: runtime files under `~/.hero_core/` (e.g., `cache/*.json`, `hero.log`).

## Build, Test, and Development Commands
- Setup: `./setup_optimized_fixed.sh` — ensures exec perms, symlink, and checks `jq`.
- Launch (optimized): `./hero_optimized` or `./launch_hero_optimized_fixed.sh` — starts the dashboard.
- Run monitors directly: `python3 monitors/claude_usage_monitor_optimized.py`.
- Lint shell: `shellcheck hero_core_optimized_fixed.sh launch_hero_optimized_fixed.sh`.
- Lint Python: `flake8 monitors/*.py` (install with `pip install flake8`).

## Coding Style & Naming Conventions
- Bash: use safe patterns (quote variables, prefer `$(...)`, avoid Useless Use of `cat`). Keep functions small and cohesive.
- Python: PEP 8, 4-space indentation, meaningful names. Keep modules single-responsibility.
- Filenames: optimized scripts use the `_optimized_fixed` suffix; monitors follow `*_monitor_optimized.py`.
- Formatting tools: `shellcheck` for bash; `flake8`/`black` optional for Python.

## Testing Guidelines
- Smoke tests: launch with `./launch_hero_optimized_fixed.sh` and verify sections render without errors.
- Monitors: run each script to confirm JSON output and cache updates in `~/.hero_core/cache/`.
- Suggested structure for future unit tests: `tests/` with `test_*.py` (pytest), and shell checks via CI.

## Commit & Pull Request Guidelines
- Commits: imperative mood and concise subjects (e.g., "Add optimized version"). Keep body focused on rationale and impact.
- PRs: include summary, before/after notes (screenshots for UI/ASCII changes), steps to validate, and any related issues/links.
- Scope: one logical change per PR; update docs when behavior or commands change.

## Security & Configuration Tips
- Dependencies: requires `python3` and `psutil`; `jq` recommended (`brew install jq`).
- Platform: optimized for macOS; some commands (e.g., `open`, `top -l`) are macOS-specific.
- Secrets: do not hardcode tokens; prefer environment variables and local config files ignored by git.
