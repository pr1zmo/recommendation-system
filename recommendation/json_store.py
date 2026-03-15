import json
from pathlib import Path

from django.conf import settings


USERS_PATH = settings.BASE_DIR / "data" / "users.json"
EVENTS_PATH = settings.BASE_DIR / "www" / "data3.json"


def _read_json(path: Path, default):
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    temp_path.replace(path)


def load_users_payload():
    payload = _read_json(USERS_PATH, {"meta": {"version": 1, "count": 0}, "users": []})
    payload.setdefault("meta", {})
    payload.setdefault("users", [])

    for user in payload["users"]:
        user.setdefault("username", "")
        user.setdefault("password", "")
        user.setdefault("preferences", {})
        history = user.setdefault("history", {})
        
        # Migrate viewedEventIds to dictionary if it's a list
        viewed_events = history.setdefault("viewedEventIds", {})
        if isinstance(viewed_events, list):
            history["viewedEventIds"] = {str(event_id): 0 for event_id in viewed_events}

        history.setdefault("likedEventIds", [])
        history.setdefault("savedEventIds", [])
        history.setdefault("dismissedEventIds", [])
        history.setdefault("dislikedEventIds", [])
        history.setdefault("attendedEventIds", [])
        user.setdefault("recommendedEventIds", [])
        user.setdefault("nextRecommendation", None)

    return payload


def save_users_payload(payload):
    payload.setdefault("meta", {})
    payload.setdefault("users", [])
    payload["meta"]["count"] = len(payload["users"])
    _write_json(USERS_PATH, payload)


def load_events_payload():
    payload = _read_json(EVENTS_PATH, {"meta": {}, "events": []})
    payload.setdefault("meta", {})
    payload.setdefault("events", [])
    return payload


def get_user_by_id(users_payload, user_id):
    return next((user for user in users_payload["users"] if user.get("id") == user_id), None)


def get_user_by_username(users_payload, username):
    normalized = username.strip().casefold()
    return next(
        (user for user in users_payload["users"] if str(user.get("username", "")).strip().casefold() == normalized),
        None,
    )


def get_event_by_id(events_payload, event_id):
    return next((event for event in events_payload["events"] if str(event.get("id")) == str(event_id)), None)


def _add_unique(items, value):
    if value not in items:
        items.append(value)


def _remove_value(items, value):
    if value in items:
        items.remove(value)


def apply_event_action(user, event_id, action, duration=0):
    history = user.setdefault("history", {})
    viewed = history.setdefault("viewedEventIds", {})
    if isinstance(viewed, list):
        # Fallback migration if we somehow hit this with a legacy list
        viewed = {str(e_id): 0 for e_id in viewed}
        history["viewedEventIds"] = viewed

    liked = history.setdefault("likedEventIds", [])
    disliked = history.setdefault("dislikedEventIds", [])
    dismissed = history.setdefault("dismissedEventIds", [])
    attended = history.setdefault("attendedEventIds", [])

    if action == "view":
        # Cumulative additions
        current_duration = viewed.get(event_id, 0)
        viewed[event_id] = current_duration + duration
        return
    else:
        # For non-view actions, still log it in viewed with 0 additional time if it wasn't there
        if event_id not in viewed:
            viewed[event_id] = 0

    if action == "like":
        if event_id in liked:
            _remove_value(liked, event_id)
        else:
            _add_unique(liked, event_id)
            _remove_value(disliked, event_id)
            _remove_value(dismissed, event_id)
        return

    if action == "dislike":
        if event_id in disliked:
            _remove_value(disliked, event_id)
            _remove_value(dismissed, event_id)
        else:
            _add_unique(disliked, event_id)
            _add_unique(dismissed, event_id)
            _remove_value(liked, event_id)
        return

    if action == "attend":
        _add_unique(attended, event_id)
        return

    raise ValueError(f"Unsupported action: {action}")


def public_user(user):
    history = user.get("history", {})
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("name"),
        "countryCode": user.get("countryCode"),
        "city": user.get("city"),
        "preferences": user.get("preferences", {}),
        "history": {
            "viewedEventIds": history.get("viewedEventIds", {}),
            "likedEventIds": history.get("likedEventIds", []),
            "savedEventIds": history.get("savedEventIds", []),
            "dismissedEventIds": history.get("dismissedEventIds", []),
            "dislikedEventIds": history.get("dislikedEventIds", []),
            "attendedEventIds": history.get("attendedEventIds", []),
        },
        "nextRecommendation": user.get("nextRecommendation"),
        "recommendedEventIds": user.get("recommendedEventIds", []),
    }