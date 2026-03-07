import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TICKETMASTER_KEY")
API_URL = f"https://app.ticketmaster.com/discovery/v2/events.json?apikey={API_KEY}"

print(API_URL)

response = requests.get(API_URL)
print(response.status_code)

if response.ok:
	print(json.loads(response.content))