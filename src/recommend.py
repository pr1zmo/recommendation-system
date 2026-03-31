import json
import random
from pathlib import Path

'''
    Candidate generation
    Feature retrieval
    Filtering
    Model inference
    Pointwise scoring and ranking
    Listwise ranking
'''

# Score=(WI​×InterestScore)+(WL​×LocationScore)+(WS​×SocialScore)

# most_interestsTags = {"sports", "soccer", "entertainement"}
# clicked_tags = {"music", "nightlife", "dance"}

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_FILE = _PROJECT_ROOT / "data" / "users.json"
EVENTS_FILE = _PROJECT_ROOT / "data" / "data3.json"


def _load_users() -> list:
    with open(USERS_FILE, "r") as f:
        return json.load(f).get("users", [])


def _load_events() -> list:
    with open(EVENTS_FILE, "r") as events:
        return json.load(events).get("events", [])

def candidate_generation(userId):
    '''
    Candidate generation: narrow down the scope of the recommended items
        to match the user's most clicked tags...
    '''
    users = _load_users()
    for i in users:
        if i["id"] == userId:
            return i
    print("Couldn't find that user")
    return None


def randomRecommend(limit: int = 20):
    events = _load_events()
    if len(events) <= limit:
        random.shuffle(events)
        return events
    return random.sample(events, limit)

def mapRecommend(location):
    return [event for event in _load_events() if event.get("countryCode") == location]

def score(userTypes: list, userLocation=None):
    if userTypes is None:
        if userLocation is None:
            return randomRecommend()
        return mapRecommend(userLocation)
    return relativeTypes(userTypes)

def relativeTypes(tags: list):
    types = set(tags)
    ev_list = []
    for event in _load_events():
        if event.get("segment") in types or event.get("genre") in types:
            ev_list.append(event)

    if len(ev_list) <= 20:
        random.shuffle(ev_list)
        return ev_list
    return random.sample(ev_list, 20)

def recommend():
    user = candidate_generation('user-001')
    if user is None:
        return randomRecommend()

    pref = user["preferences"]
    seg = (pref["segments"])
    genres = (pref["genres"])
    tags = seg + genres
    return relativeTypes(tags)
    # with open('bruh.json', 'wb') as f:
    #     json.dump(relativeTypes(["Comedy", "Country"]), f)

if __name__ == "__main__":
    # print(mapRecommend("MA"))
    print(recommend())