import json
import math
from pathlib import Path
from sklearn.preprocessing import normalize
from generator.generate import types, category, sub_category

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
DISLIKED_GENRE = -5

EVENTS_FILE = str(_PROJECT_ROOT / "data" / "data3.json")
USERS_FILE = str(_PROJECT_ROOT / "data" / "users.json")


def _get_user_data(user):
    """Helper to load and find user by ID, reducing redundancy."""
    with open(USERS_FILE, "r") as usr:
        data = json.load(usr)
    
    for entry in data["users"]:
        if entry["id"] == user:
            return entry
    
    return None


def getSegments(user, multiplier) -> dict:
    userData = _get_user_data(user)
    
    if userData is None:
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

def getEvents(user, multiplier, field: str) -> dict:
    userData = _get_user_data(user)
    
    if userData is None:
        return None
    
    likes = userData["history"].get(field, [])
    
    # Load events from data3.json
    with open(EVENTS_FILE, "r") as events_file:
        events_data = json.load(events_file)
    
    # Build a map of event_id -> event for fast lookup
    event_by_id = {}
    for event in events_data.get("events", []):
        event_id = event.get("id")
        if event_id:
            event_by_id[event_id] = event
    
    # Extract segment and genre from liked events
    profile = {}
    for liked_id in likes:
        event = event_by_id.get(liked_id)
        if not event:
            continue

        genre = event.get("genre")
        if genre:
            profile[genre] = profile.get(genre, 0) + multiplier
    
    return profile

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
    prof.update(getEvents(user, LIKED, "likedEventIds"))
    prof.update(getEvents(user, DISLIKED, "dislikedEventIds"))
    prof.update(getEvents(user, ATTENDED, "attendedEventIds"))

    return prof
    # prof.append(getSegments(user, EXPLICIT))

class Matrix:
    pass

def matrixMult(m1, m2):
    pass

def coldStart() -> list:
    pass

def userEventMatrix(users, events):
    pass

def normalize_word(item: str) -> str:
    res = ''.join([i for i in item if i.isalpha() or i.isspace() or i == '&'])
    return res.lower()

def getEventVocabulary() -> dict:
    seen = []

    # 1. Collect genres from the events file
    with open(EVENTS_FILE, "r") as f:
        eventsData = json.load(f)
        for event in eventsData["events"]:
            genre = event.get("genre")
            if genre and genre not in seen:
                seen.append(genre)

    # 2. Add event type values (Conference, Seminar, etc.)
    for value in types.values():
        if value not in seen:
            seen.append(value)

    # 3. Add sub-category values (Pop, Rock & Roll, etc.) — skip the main category keys
    for subcats in sub_category.values():
        for item in subcats:
            if item not in seen:
                seen.append(normalize_word(item))

    # Build indexed vocabulary dict
    vocabulary = {}
    for index, genre in enumerate(seen):
        vocabulary[genre] = index

    return vocabulary

# def getVectorList(vocabulary: dict, userProfile: dict) -> list:
#     return [max(0, userProfile.get(key, 0)) for key in vocabulary]

def l2_normalize(vector: list) -> list:
    magnitude = sum(x ** 2 for x in vector) ** 0.5
    if magnitude == 0:
        return vector
    return [x / magnitude for x in vector]

def buildVectors(user):
    vocabulary = getEventVocabulary()
    userProfile = buildUserProfile(user)
    vectorList = [max(0, userProfile.get(key, 0)) for key in vocabulary]
    normalized = l2_normalize(vectorList)
    return normalized

def getEventVector(seg: str, genre: str, userVector: list) -> list:
    vocabulary = getEventVocabulary()
    userGenres = set()
    if seg:
        userGenres.add(normalize_word(seg))
    if genre:
        userGenres.add(normalize_word(genre))

    lst = []
    for key in vocabulary:
        if normalize_word(key) in userGenres:
            lst.append(1)
        else:
            lst.append(0)
    return lst

def scoreEvent(event, user_vector, vocabulary):
    score = 0
    for tag in [event.get("genre"), event.get("segment")]:
        if tag and tag in vocabulary:
            score += user_vector[vocabulary[tag]]
    return score


def recommend(user, vocabulary, events_data=None):
    """Return the top-20 event IDs with their scores.
    If events_data is provided (list of event dicts), use it directly;
    otherwise load from EVENTS_FILE.
    """
    if events_data is None:
        with open(EVENTS_FILE, "r") as f:
            events_data = json.load(f).get("events", [])

    events_scores = {}
    userVector = buildVectors(user)

    for event in events_data:
        score = scoreEvent(event, userVector, vocabulary)
        events_scores[event["id"]] = score

    sorted_items = sorted(events_scores.items(), key=lambda x: x[1], reverse=True)

    return dict(sorted_items[:20])