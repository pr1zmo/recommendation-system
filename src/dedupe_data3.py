import argparse
import json
from pathlib import Path
import os


DEFAULT_INPUT_PATH = Path("www/data3.json")
# DEFAULT_INPUT_PATH = os.path("../www/data3.json")
PLACEHOLDER_DESCRIPTION = "no description available."


def normalize_text(value):
	if not isinstance(value, str):
		return ""
	return " ".join(value.split()).strip().casefold()


def build_duplicate_keys(event):
	keys = set()
	if not isinstance(event, dict):
		return keys

	title = normalize_text(event.get("name"))
	description = normalize_text(event.get("description"))
	image_url = normalize_text(event.get("imageUrl"))

	if title:
		keys.add(("title", title))

	if description and description != PLACEHOLDER_DESCRIPTION:
		keys.add(("description", description))

	if image_url:
		keys.add(("image", image_url))

	return keys


def load_payload(path):
	with path.open("r", encoding="utf-8") as handle:
		payload = json.load(handle)

	if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
		raise ValueError("Expected a JSON object with an events array.")

	payload.setdefault("meta", {})
	return payload


def dedupe_events(events):
	seen_keys = set()
	unique_events = []
	stats = {
		"removed": 0,
		"removedByTitle": 0,
		"removedByDescription": 0,
		"removedByImage": 0,
	}

	for event in events:
		event_keys = build_duplicate_keys(event)
		if not event_keys:
			unique_events.append(event)
			continue

		duplicate_reason = None
		for key in event_keys:
			if key in seen_keys:
				duplicate_reason = key[0]
				break

		if duplicate_reason is not None:
			stats["removed"] += 1
			if duplicate_reason == "title":
				stats["removedByTitle"] += 1
			elif duplicate_reason == "description":
				stats["removedByDescription"] += 1
			elif duplicate_reason == "image":
				stats["removedByImage"] += 1
			continue

		seen_keys.update(event_keys)
		unique_events.append(event)

	return unique_events, stats


def save_payload(path, payload):
	temp_path = path.with_suffix(path.suffix + ".tmp")
	with temp_path.open("w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2, ensure_ascii=False)
		handle.write("\n")
	temp_path.replace(path)


def parse_args():
	parser = argparse.ArgumentParser(description="Remove duplicate events from data3.json.")
	parser.add_argument("path", nargs="?", default=str(DEFAULT_INPUT_PATH), help="Path to the JSON file to clean.")
	return parser.parse_args()


def main():
	args = parse_args()
	path = Path(args.path)
	payload = load_payload(path)
	unique_events, stats = dedupe_events(payload["events"])

	payload["events"] = unique_events
	payload["meta"]["count"] = len(unique_events)
	payload["meta"]["dedupeRemoved"] = stats["removed"]
	payload["meta"]["dedupeRemovedByTitle"] = stats["removedByTitle"]
	payload["meta"]["dedupeRemovedByDescription"] = stats["removedByDescription"]
	payload["meta"]["dedupeRemovedByImage"] = stats["removedByImage"]

	save_payload(path, payload)

	print(
		f"Removed {stats['removed']} duplicates from {path} "
		f"(title={stats['removedByTitle']}, "
		f"description={stats['removedByDescription']}, "
		f"image={stats['removedByImage']})"
	)


if __name__ == "__main__":
	main()