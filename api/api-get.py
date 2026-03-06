import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# The API endpoint URL
API_KEY = os.getenv('EVENTBRITE_API_KEY')  # Make sure to set your API key in the environment variables
api_url = f"https://www.eventbriteapi.com/v3/users/me/?token={API_KEY}"

print(api_url)

# Make the GET request
response = requests.get(api_url)

print(response)

# Check the status code
if response.status_code == 200:
    # Parse the JSON response into a Python dictionary
    data = response.json()

    # Access and use the data
    # print(f"Number of people in space: {data['number']}")
    print(data)

else:
    # Handle the error
    print(f"API request failed with status code: {response.status_code}")