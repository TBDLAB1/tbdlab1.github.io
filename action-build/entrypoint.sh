#!/bin/sh
# Fail immediately if any command errors, so a broken build surfaces as a
# failed workflow run instead of silently deploying stale content.
set -e

cd /github/workspace
echo "Install Python dependencies..."
pip3 install -r requirements.txt
echo "Building the website..."
python3 build.py
echo "Done!"