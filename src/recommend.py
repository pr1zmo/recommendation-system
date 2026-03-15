import json
import random

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

USERS_FILE = "data/users.json"
EVENTS_FILE = "data/data3.json"

def candidate_generation(userId):
    '''
    Candidate generation: narrow down the scope of the recommended items
        to match the user's most clicked tags...
    '''
    with open(USERS_FILE, 'r') as f:
        content = json.load(f)
        users = content['users']
        for i in users:
            if (i['id'] == userId):
                return i
        print("Couldn't find that user")
    return None

def randomRecommend():
    pass

def mapRecommend(location):
    rec = []
    with open(EVENTS_FILE) as events:
        content = json.load(events)
        for i in content['events']:
            # print(i)
            if (i['countryCode'] == location):
                rec.append(i)
    return rec

def score(userTypes: list) -> float:
    if (userTypes == None):
        if (userLocation == None):
            return randomRecommend()
        else:
            return mapRecommend(userLocation)
    pass

def relativeTypes(tags: list):
    types = tags
    ev_list = []
    with open(EVENTS_FILE) as events:
        content = json.load(events)
        for i in content["events"]:
            if len(ev_list) == 20:
                break
            if (i["segment"] in types or i["genre"] in types):
                ev_list.append(i)
    random.shuffle(ev_list)
    return ev_list

def recommend():
    user = candidate_generation('user-001')
    pref = user["preferences"]
    tags = []
    seg = (pref["segments"])
    genres = (pref["genres"])
    tags = seg + genres
    print(relativeTypes(tags))
    # with open('bruh.json', 'wb') as f:
    #     json.dump(relativeTypes(["Comedy", "Country"]), f)

if __name__ == "__main__":
    # print(mapRecommend("MA"))
    recommend()