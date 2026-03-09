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

COUNTRY_CODES = [
	"US", "CA", "GB", "DE", "FR", "NL", "ES", "AU", "NZ", "MX"
]

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


def load_output_payload(path):
	if not os.path.exists(path):
		return {"meta": {"count": 0}, "events": []}

	with open(path, "r", encoding="utf-8") as handle:
		payload = json.load(handle)

	if not isinstance(payload, dict):
		raise ValueError("www/data3.json must contain a JSON object.")

	payload.setdefault("meta", {})
	payload.setdefault("events", [])
	if not isinstance(payload["events"], list):
		raise ValueError("www/data3.json must contain an events array.")

	return payload


def build_event_keys(event):
	if not isinstance(event, dict):
		return set()

	keys = set()
	event_id = event.get("id")
	if event_id is not None:
		keys.add(("id", str(event_id)))

	url = (event.get("url") or "").strip()
	if url:
		keys.add(("url", url))

	name = (event.get("name") or "").strip().casefold()
	local_date = event.get("localDate") or ""
	country_code = event.get("countryCode") or ""
	segment = (event.get("segment") or "").strip().casefold()
	if name and local_date:
		keys.add(("signature", name, local_date, country_code, segment))

	return keys


def merge_events(path, new_events, meta):
	payload = load_output_payload(path)
	existing_events = payload["events"]
	seen_keys = set()

	for existing_event in existing_events:
		seen_keys.update(build_event_keys(existing_event))

	unique_new_events = []
	for event in new_events:
		event_keys = build_event_keys(event)
		if not event_keys or event_keys & seen_keys:
			continue
		unique_new_events.append(event)
		seen_keys.update(event_keys)

	existing_events.extend(unique_new_events)
	payload["meta"].update(meta)
	payload["meta"]["count"] = len(existing_events)
	payload["meta"]["lastAddedCount"] = len(unique_new_events)

	with open(path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2)
		handle.write("\n")

	return len(unique_new_events)

try:
	selected_country = random.choice(COUNTRY_CODES)

	params = {
		"apikey": API_KEY,
		"countryCode": selected_country,
		"size": 80,
		"sort": "random",
	}

	events = fetch_events(params)

	# One unfiltered random search returns a mixed batch across segments when available.
	if len(events) < 12:
		params.pop("countryCode", None)
		events = fetch_events(params)

	compact_events = [compact_event(event) for event in events if event.get("name")]

	random.shuffle(compact_events)
	observed_segments = sorted({event.get("segment") for event in compact_events if event.get("segment")})
	observed_genres = sorted({event.get("genre") for event in compact_events if event.get("genre")})

	added_count = merge_events(
		"www/data3.json",
		compact_events,
		{
			"countryCode": selected_country if params.get("countryCode") else None,
			"queryType": "mixed-random",
			"lastBatchCount": len(compact_events),
			"segments": observed_segments,
			"genresSample": observed_genres[:12],
		},
	)

	print(
		f"Added {added_count} new events from a mixed random batch of {len(compact_events)} "
		f"to www/data3.json (country={selected_country if params.get('countryCode') else 'any'})"
	)
except requests.RequestException as error:
	print(f"Request failed: {error}")
except ValueError as error:
	print(f"Failed to parse JSON response: {error}")
