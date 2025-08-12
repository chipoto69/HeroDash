#!/bin/bash

# Setup script for optimized Hero Core Dashboard

echo "Setting up optimized Hero Core Dashboard..."

# Make all scripts executable
chmod +x /Users/rudlord/Hero_dashboard/hero_core_optimized_fixed.sh
chmod +x /Users/rudlord/Hero_dashboard/launch_hero_optimized_fixed.sh
chmod +x /Users/rudlord/Hero_dashboard/monitors/claude_usage_monitor_optimized.py
chmod +x /Users/rudlord/Hero_dashboard/monitors/github_activity_monitor_optimized.py

echo "✓ Made all scripts executable"

# Create symlink for hero command to use optimized version
if [ ! -f "/Users/rudlord/Hero_dashboard/hero_optimized" ]; then
    ln -s /Users/rudlord/Hero_dashboard/launch_hero_optimized_fixed.sh /Users/rudlord/Hero_dashboard/hero_optimized
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
echo "  ./launch_hero_optimized_fixed.sh"
echo ""
echo "Key optimizations implemented:"
echo "  ✓ Command caching to reduce system calls"
echo "  ✓ Better JSON parsing with jq (when available)"
echo "  ✓ Improved monitor script performance"
echo "  ✓ Reduced redundant operations"
echo "  ✓ Better error handling and caching"
echo "  ✓ Fixed compatibility issues"