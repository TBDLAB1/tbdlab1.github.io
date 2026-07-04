import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_PATH = os.path.join(BASE_PATH, 'docs')
API_KEY = os.getenv('INPUT_API_KEY', '') or '573caf0af340ca84b18f5926de9aff5257262661'

DATA_URL = 'https://docs.google.com/spreadsheets/d/1SaAs1CaSkPwv4Ktg4z0P7ETSZl1o7yW0qtFJakNh7lM/edit?usp=sharing'
