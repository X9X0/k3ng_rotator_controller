#!/bin/bash
# Quick script to clean Python bytecode cache
# Useful during development when switching branches or after git pull

echo "Cleaning Python bytecode cache..."

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove .pyc files
find . -type f -name "*.pyc" -delete 2>/dev/null

# Remove .pyo files (optimized bytecode)
find . -type f -name "*.pyo" -delete 2>/dev/null

echo "✓ Cache cleared successfully!"
