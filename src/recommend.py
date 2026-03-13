import json

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
EVENTS_FILE = "data/"

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
        # print(users[0]['id'])
    return None

def randomRecommend():
    pass

def mapRecommend(location):
    with open()

def score(userTypes: list) -> float:
    if (userTypes == None):
        if (userLocation == None):
            return randomRecommend()
        else:
            return mapRecommend(userLocation)
    pass

def recommend():
    print(candidate_generation("user-005"))

if __name__ == "__main__":
    recommend()