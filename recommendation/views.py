import json
import sys
from pathlib import Path

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

# Make src/ importable so we can call logic.recommend()
_SRC_DIR = str(Path(settings.BASE_DIR) / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from recommendation.json_store import (
    apply_event_action,
    get_event_by_id,
    get_user_by_id,
    get_user_by_username,
    load_events_payload,
    load_users_payload,
    public_user,
    save_users_payload,
)


SESSION_USER_KEY = "json_user_id"


@require_GET
def home(request):
    return render(request, 'index.html')


@require_GET
def data_json(request):
    data_path = settings.BASE_DIR / "www" / "data3.json"

    with data_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return JsonResponse(payload)


def _current_user(request, users_payload):
    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        return None
    return get_user_by_id(users_payload, user_id)


def _parse_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body.")


@require_GET
def bootstrap(request):
    users_payload = load_users_payload()
    events_payload = load_events_payload()
    user = _current_user(request, users_payload)

    return JsonResponse(
        {
            "isAuthenticated": user is not None,
            "user": public_user(user) if user else None,
            "events": events_payload.get("events", []),
        }
    )


@require_POST
def login_view(request):
    try:
        body = _parse_json_body(request)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))

    if not username or not password:
        return JsonResponse({"error": "Username and password are required."}, status=400)

    users_payload = load_users_payload()
    user = get_user_by_username(users_payload, username)

    if not user or str(user.get("password", "")) != password:
        return JsonResponse({"error": "Invalid username or password."}, status=401)

    request.session[SESSION_USER_KEY] = user.get("id")
    return JsonResponse({"user": public_user(user)})


@require_POST
def logout_view(request):
    request.session.pop(SESSION_USER_KEY, None)
    return JsonResponse({"ok": True})


@require_POST
def event_action(request, event_id):
    try:
        body = _parse_json_body(request)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    action = str(body.get("action", "")).strip()
    duration = int(body.get("duration", 0)) if str(body.get("duration", 0)).isdigit() else 0

    if action not in {"view", "like", "dislike", "attend"}:
        return JsonResponse({"error": "Unsupported action."}, status=400)

    users_payload = load_users_payload()
    user = _current_user(request, users_payload)
    if not user:
        return JsonResponse({"error": "Authentication required."}, status=401)

    events_payload = load_events_payload()
    if not get_event_by_id(events_payload, event_id):
        return JsonResponse({"error": "Event not found."}, status=404)

    apply_event_action(user, str(event_id), action, duration)
    save_users_payload(users_payload)

    return JsonResponse({"user": public_user(user)})


@require_POST
def update_preferences(request):
    try:
        body = _parse_json_body(request)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    segments = body.get("segments")
    if not isinstance(segments, list):
        return JsonResponse({"error": "Segments must be a list."}, status=400)

    users_payload = load_users_payload()
    user = _current_user(request, users_payload)
    if not user:
        return JsonResponse({"error": "Authentication required."}, status=401)

    user.setdefault("preferences", {})
    user["preferences"]["segments"] = [str(s).strip() for s in segments if str(s).strip()]
    
    save_users_payload(users_payload)

    return JsonResponse({"user": public_user(user)})


@require_GET
def recommend_view(request):
    from logic import recommend, getEventVocabulary

    users_payload = load_users_payload()
    user = _current_user(request, users_payload)
    if not user:
        return JsonResponse({"error": "Authentication required."}, status=401)

    events_payload = load_events_payload()
    events_list = events_payload.get("events", [])
    vocabulary = getEventVocabulary()

    scored = recommend(user["id"], vocabulary, events_data=events_list)

    # Build a lookup of event id -> event dict
    event_by_id = {str(e.get("id")): e for e in events_list}

    recommended_events = []
    for event_id in scored:
        event = event_by_id.get(str(event_id))
        if event:
            recommended_events.append(event)

    # Persist on the user object
    user["recommendedEventIds"] = list(scored.keys())
    user["nextRecommendation"] = user["recommendedEventIds"][0] if user["recommendedEventIds"] else None
    save_users_payload(users_payload)

    return JsonResponse({"events": recommended_events, "user": public_user(user)})
