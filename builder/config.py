import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_PATH = os.path.join(BASE_PATH, 'docs')

# Secrets are injected by the Builder workflow as the API_KEY / DATA_URL action
# inputs (exposed to the container as INPUT_API_KEY / INPUT_DATA_URL), so they
# are never committed to the repository. For local builds, set them yourself:
#   INPUT_API_KEY=... INPUT_DATA_URL=... python3 build.py
API_KEY = os.getenv('INPUT_API_KEY', '')
DATA_URL = os.getenv('INPUT_DATA_URL', '')
