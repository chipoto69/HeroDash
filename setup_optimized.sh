#!/bin/bash

# Setup script for optimized Hero Core Dashboard

echo "Setting up optimized Hero Core Dashboard..."

# Make all scripts executable
HERO_DASHBOARD_DIR="${HERO_DASHBOARD_DIR:-/Users/rudlord/Hero_dashboard}"
chmod +x "$HERO_DASHBOARD_DIR/hero_core_optimized.sh"
chmod +x "$HERO_DASHBOARD_DIR/launch_hero_optimized.sh"
chmod +x "$HERO_DASHBOARD_DIR/monitors/claude_usage_monitor_optimized.py"
chmod +x "$HERO_DASHBOARD_DIR/monitors/github_activity_monitor_optimized.py"

echo "✓ Made all scripts executable"

# Create symlink for hero command to use optimized version
if [ ! -f "$HERO_DASHBOARD_DIR/hero_optimized" ]; then
    ln -s "$HERO_DASHBOARD_DIR/launch_hero_optimized.sh" "$HERO_DASHBOARD_DIR/hero_optimized"
    echo "✓ Created hero_optimized symlink"
fi

# Verify jq is installed (for better JSON parsing performance)
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq is not installed. For better performance, install jq:"
    echo "   brew install jq  # macOS"
    echo "   sudo apt-get install jq  # Ubuntu/Debian"
else
    echo "✓ jq is installed (for faster JSON parsing)"
fi

echo ""
echo "Optimized Hero Core Dashboard setup complete!"
echo ""
echo "To launch the optimized version:"
echo "  ./hero_optimized"
echo "  or"
echo "  ./launch_hero_optimized.sh"
echo ""
echo "Key optimizations implemented:"
echo "  ✓ Command caching to reduce system calls"
echo "  ✓ Better JSON parsing with jq (when available)"
echo "  ✓ Improved monitor script performance"
echo "  ✓ Reduced redundant operations"
echo "  ✓ Better error handling and caching"