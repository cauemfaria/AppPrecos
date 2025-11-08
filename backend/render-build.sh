#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright and Chromium browser
playwright install chromium
playwright install-deps chromium

echo "Build completed successfully!"

