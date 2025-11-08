#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright and Chromium browser
playwright install chromium

# Note: playwright install-deps requires root and doesn't work on Render
# Chromium should work in headless mode without system dependencies

echo "Build completed successfully!"

