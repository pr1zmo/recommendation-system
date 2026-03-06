# 

""" 
import json
import requests

# The API endpoint URL
api_url = "https://www.eventbriteapi.com/v3/users/me/?token=MYTOKEN"

# Make the GET request
response = requests.get(api_url)

# Check the status code
if response.status_code == 200:
    # Parse the JSON response into a Python dictionary
    data = response.json()

    # Access and use the data
    print(f"Number of people in space: {data['number']}")
    for person in data['people']:
        print(f"- {person['name']} on {person['craft']}")

else:
    # Handle the error
    print(f"API request failed with status code: {response.status_code}")
"""