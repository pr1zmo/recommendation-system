import os
import requests
import json
import random
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TICKETMASTER_KEY")

if not API_KEY:
    raise ValueError("Missing TICKETMASTER_KEY in environment variables.")

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# A mixed pool so each run can pull different combinations.
COUNTRY_CODES = [
    "US", "CA", "GB", "DE", "FR", "NL", "ES", "AU", "NZ", "MX"
]

SEGMENT_IDS = {
    "music": "KZFzniwnSyZfZ7v7nJ",
    "sports": "KZFzniwnSyZfZ7v7nE",
    "arts-theatre": "KZFzniwnSyZfZ7v7na",
    "film": "KZFzniwnSyZfZ7v7nn",
    "misc": "KZFzniwnSyZfZ7v7n1",
}


def choose_image(raw_images):
    images = raw_images or []
    preferred = [img for img in images if img.get("ratio") == "16_9"]
    candidates = preferred or images
    if not candidates:
        return None

    # Pick the largest available candidate by area.
    best = max(candidates, key=lambda img: (img.get("width", 0) * img.get("height", 0)))
    return best.get("url")


def compact_event(raw_event):
    classifications = raw_event.get("classifications") or []
    primary = classifications[0] if classifications else {}
    segment = (primary.get("segment") or {}).get("name")
    genre = (primary.get("genre") or {}).get("name")
    status = ((raw_event.get("dates") or {}).get("status") or {}).get("code")

    return {
        "id": raw_event.get("id"),
        "name": raw_event.get("name"),
        "url": raw_event.get("url"),
        "description": raw_event.get("info") or raw_event.get("pleaseNote") or "No description available.",
        "localDate": ((raw_event.get("dates") or {}).get("start") or {}).get("localDate"),
        "countryCode": ((((raw_event.get("_embedded") or {}).get("venues") or [{}])[0].get("country") or {}).get("countryCode")),
        "segment": segment,
        "genre": genre,
        "status": status,
        "imageUrl": choose_image(raw_event.get("images")),
    }


def fetch_events(params):
    response = requests.get(BASE_URL, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    return payload.get("_embedded", {}).get("events", [])

try:
    selected_country = random.choice(COUNTRY_CODES)
    selected_segment_key = random.choice(list(SEGMENT_IDS.keys()))
    selected_segment_id = SEGMENT_IDS[selected_segment_key]

    params = {
        "apikey": API_KEY,
        # "countryCode": selected_country,
        "segmentId": selected_segment_id,
        "size": 80,
        "sort": "random",
    }

    events = fetch_events(params)

    # Fallback: if a combo returns little/no data, retry without segment restriction.
    if len(events) < 12:
        params.pop("segmentId", None)
        events = fetch_events(params)

    compact_events = [compact_event(event) for event in events if event.get("name")]

    random.shuffle(compact_events)

    output_payload = {
        "meta": {
            "countryCode": selected_country,
            "segment": selected_segment_key,
            "count": len(compact_events),
        },
        "events": compact_events,
    }

    with open("www/data.json", "w", encoding="utf-8") as output:
        json.dump(output_payload, output, indent=2)

    print(
        f"Saved {len(compact_events)} compact events to www/data.json "
        f"(country={selected_country}, segment={selected_segment_key})"
    )
except requests.RequestException as error:
    print(f"Request failed: {error}")
except ValueError as error:
    print(f"Failed to parse JSON response: {error}")
