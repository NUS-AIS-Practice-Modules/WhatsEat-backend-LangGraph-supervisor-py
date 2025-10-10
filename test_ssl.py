import requests
from whats_eat.app.env_loader import load_env
import os
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings()

load_env()

uri = os.getenv('NEO4J_URI').replace('neo4j+s://', 'https://')
user = os.getenv('NEO4J_USER')
pwd = os.getenv('NEO4J_PASSWORD')

print(f"Testing connection to: {uri}")

try:
    response = requests.get(uri, verify=False)
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {response.headers}")
except Exception as e:
    print(f"Error: {str(e)}")