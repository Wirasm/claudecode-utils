#!/bin/bash

# Clean build artifacts script for Dylan project

echo "🧹 Cleaning build artifacts..."

# Remove egg-info directories
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "✓ Removed egg-info directories"

# Remove pycache directories
find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
echo "✓ Removed __pycache__ directories"

# Remove .pyc files
find . -type f -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
echo "✓ Removed .pyc files"

# Remove build and dist directories if they exist
rm -rf build/ dist/ 2>/dev/null || true
echo "✓ Removed build and dist directories"

# Remove .ruff_cache if it exists
rm -rf .ruff_cache 2>/dev/null || true
echo "✓ Removed .ruff_cache"

echo "🎉 Cleanup complete!"