import json

def similarity() -> float:
    return .011245

'''
Recommendation formual:

    attendedEventIds: 5.0
    likedEventIds and savedEventIds: 3.0
    viewedEventIds: 1.0+log(duration) (to factor in the time spent reading)
    dislikedEventIds and dismissedEventIds: -5.0

I will Calculate a single mathematical vector representing the user's overall taste (Vu).
I must do this by taking the vectors of the specific events they have interacted with
(Ve), multiplying them by the interaction weight you defined above (W),
and adding them all together alongside their explicit JSON preferences (P).
'''

'''
| Action         | Effect |
| -------------- | ------ |
| liked event    | +3     |
| attended event | +4     |
| viewed event   | +1     |
| disliked event | -3     |
| explicit genre | +5     |
| disliked genre | -5     |

'''

LIKED = 3
ATTENDED = 4
VIEWD = 1
DISLIKED = -3
EXPLICIT = 5
DISLIKED = -5

USERS_FILE = "data/users.json"

def getSegments(user, multiplier) -> dict:
    print(user)
    with open(USERS_FILE, "r") as usr:
        data = json.load(usr)
    
    userData = None

    for i in data['users']:
        if (i['id'] == user):
            userData = i

    if (userData == None):
        print(f"User {user} does not exist!\n")
        return None

    segments = userData["preferences"]["segments"]

    seg = {}
    for value in segments:
        if isinstance(value, dict):
            for key, weight in value.items():
                seg[key] = weight * multiplier
        else:
            seg[value] = multiplier

    return seg

def buildUserProfile(user) -> dict:
    '''
    build the user Profile based on the data in the users.json
    Should return something like this:
    {
        "Theatre": 3,
        "Comedy": 4,
        "Music": 1,
    }
    You then normalize the weights:
    '''
    prof = {}
    prof.update(getSegments(user, EXPLICIT))
    # prof.append(getSegments(user, EXPLICIT))
    print(prof)

class Matrix:
    pass

def matrixMult(m1, m2):
    pass

def coldStart() -> list:
    pass

def userEventMatrix(users, events):
    pass

buildUserProfile("user-001")