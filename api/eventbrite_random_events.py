#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


DEFAULT_ENDPOINT_TEMPLATE = "https://www.eventbriteapi.com/v3/events/{event_id}/"
DEFAULT_OUTPUT_PATH = Path("www/ev-data.json")
DEFAULT_STATE_PATH = Path("data/eventbrite_random_state.json")
DEFAULT_MIN_EVENT_ID = 10**12
DEFAULT_MAX_EVENT_ID = (10**13) - 1
DEFAULT_TIMEOUT = 20
HOURLY_LIMIT = 2000
DAILY_LIMIT = 48000
HOURLY_WINDOW_SECONDS = 60 * 60
DAILY_WINDOW_SECONDS = 24 * 60 * 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe randomized Eventbrite event IDs while staying under the "
            "published 2,000/hour and 48,000/day rate limits."
        )
    )
    parser.add_argument(
        "--token",
        default=os.getenv("EVENTBRITE_OAUTH_TOKEN") or os.getenv("PERSONAL_OAUTH_TOKEN"),
        help="Eventbrite personal OAuth token. Defaults to EVENTBRITE_OAUTH_TOKEN.",
    )
    parser.add_argument(
        "--endpoint-template",
        default=DEFAULT_ENDPOINT_TEMPLATE,
        help=(
            "URL template containing {event_id}. For teams, use "
            "https://www.eventbriteapi.com/v3/events/{event_id}/teams/"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="JSON file with the same meta/events structure already used in www/data.json.",
    )
    parser.add_argument(
        "--min-event-id",
        type=int,
        default=DEFAULT_MIN_EVENT_ID,
        help="Smallest random event ID to generate.",
    )
    parser.add_argument(
        "--max-event-id",
        type=int,
        default=DEFAULT_MAX_EVENT_ID,
        help="Largest random event ID to generate.",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help=(
            "Optional numeric prefix to bias ID generation into a denser range. "
            "Example: 198 narrows the search to 13-digit IDs that start with 198."
        ),
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=0,
        help="Stop after this many calls. Use 0 to run until interrupted.",
    )
    parser.add_argument(
        "--target-successes",
        type=int,
        default=0,
        help="Stop after this many successful responses. Use 0 to ignore.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="JSON state file used to persist rate-limit timestamps and saved IDs.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print a progress line after this many requests.",
    )
    return parser.parse_args()


def load_env() -> None:
    if load_dotenv is not None:
        load_dotenv()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state() -> dict[str, Any]:
    return {
        "request_timestamps": [],
        "saved_event_ids": [],
        "stats": {
            "attempted": 0,
            "successful": 0,
            "not_found": 0,
            "duplicates": 0,
            "rate_limited": 0,
            "request_errors": 0,
            "server_errors": 0,
            "other_errors": 0,
        },
        "last_request_at": None,
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_state()

    with path.open("r", encoding="utf-8") as handle:
        raw_state = json.load(handle)

    state = default_state()
    state.update(raw_state)
    state["stats"].update(raw_state.get("stats", {}))
    return state


def save_state(path: Path, state: dict[str, Any], request_timestamps: deque[float], saved_event_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(state)
    payload["request_timestamps"] = list(request_timestamps)
    payload["saved_event_ids"] = sorted(saved_event_ids)

    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    temp_path.replace(path)


def build_random_event_id(prefix: str, min_event_id: int, max_event_id: int) -> str:
    if prefix:
        if not prefix.isdigit():
            raise ValueError("--prefix must contain only digits.")
        suffix_length = 13 - len(prefix)
        if suffix_length <= 0:
            raise ValueError("--prefix must be shorter than 13 digits.")
        suffix_value = random.randint(0, (10**suffix_length) - 1)
        return f"{prefix}{suffix_value:0{suffix_length}d}"

    if min_event_id > max_event_id:
        raise ValueError("--min-event-id must be less than or equal to --max-event-id.")
    return str(random.randint(min_event_id, max_event_id))


def prune_timestamps(request_timestamps: deque[float], now: float) -> None:
    cutoff = now - DAILY_WINDOW_SECONDS
    while request_timestamps and request_timestamps[0] < cutoff:
        request_timestamps.popleft()


def compute_wait_seconds(request_timestamps: deque[float], now: float) -> float:
    prune_timestamps(request_timestamps, now)
    if not request_timestamps:
        return 0.0

    daily_count = len(request_timestamps)
    hourly_cutoff = now - HOURLY_WINDOW_SECONDS
    hourly_count = sum(timestamp >= hourly_cutoff for timestamp in request_timestamps)

    daily_wait = 0.0
    if daily_count >= DAILY_LIMIT:
        daily_wait = (request_timestamps[0] + DAILY_WINDOW_SECONDS) - now

    hourly_wait = 0.0
    if hourly_count >= HOURLY_LIMIT:
        hourly_index = daily_count - hourly_count
        hourly_wait = (request_timestamps[hourly_index] + HOURLY_WINDOW_SECONDS) - now

    return max(daily_wait, hourly_wait, 0.0)


def wait_until_limit_resets(request_timestamps: deque[float], next_allowed_at: float) -> float:
    now = time.time()
    wait_seconds = max(compute_wait_seconds(request_timestamps, now), max(next_allowed_at - now, 0.0))
    if wait_seconds > 0:
        print(f"Waiting {wait_seconds:.2f}s for rate limit reset.")
        time.sleep(wait_seconds)
        now = time.time()
    return now


def compact_eventbrite_event(payload: dict[str, Any], endpoint_template: str, event_id: str) -> dict[str, Any]:
    start = payload.get("start") or {}
    end = payload.get("end") or {}
    venue = payload.get("venue") or {}
    logo = payload.get("logo") or {}
    organizer = payload.get("organizer") or {}
    category = payload.get("category") or {}
    subcategory = payload.get("subcategory") or {}
    format_data = payload.get("format") or {}
    status = payload.get("status") or payload.get("resource_uri") or "unknown"

    return {
        "id": str(payload.get("id", event_id)),
        "name": payload.get("name", {}).get("text") or payload.get("name") or f"Eventbrite event {event_id}",
        "url": payload.get("url") or endpoint_template.format(event_id=event_id),
        "description": payload.get("summary") or payload.get("description", {}).get("text") or "No description available.",
        "localDate": (start.get("local") or "")[:10] or None,
        "countryCode": (venue.get("address") or {}).get("country") or (payload.get("online_event") and "ONLINE") or None,
        "segment": category.get("name") or organizer.get("name") or "Eventbrite",
        "genre": subcategory.get("name") or format_data.get("name") or None,
        "status": status,
        "imageUrl": logo.get("url"),
        "source": "eventbrite",
        "start": start.get("utc") or start.get("local"),
        "end": end.get("utc") or end.get("local"),
    }


def load_output_catalog(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"meta": {"count": 0}, "events": []}

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Output file {path} must contain a JSON object.")

    payload.setdefault("meta", {})
    payload.setdefault("events", [])
    if not isinstance(payload["events"], list):
        raise ValueError(f"Output file {path} must contain an events array.")
    return payload


def append_event(path: Path, event_payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    catalog = load_output_catalog(path)
    events = catalog["events"]

    if any(str(existing.get("id")) == str(event_payload["id"]) for existing in events if isinstance(existing, dict)):
        return False

    events.append(event_payload)
    catalog["meta"]["count"] = len(events)

    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    temp_path.replace(path)
    return True


def build_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def handle_success(
    output_path: Path,
    saved_event_ids: set[str],
    endpoint_template: str,
    event_id: str,
    payload: Any,
) -> bool:
    if not isinstance(payload, dict):
        return False

    normalized_id = str(payload.get("id", event_id))
    if normalized_id in saved_event_ids:
        return False

    event_payload = compact_eventbrite_event(payload, endpoint_template, event_id)
    if not append_event(output_path, event_payload):
        return False

    saved_event_ids.add(normalized_id)
    return True


def print_summary(state: dict[str, Any]) -> None:
    stats = state["stats"]
    print(
        "Summary: "
        f"attempted={stats['attempted']}, "
        f"successful={stats['successful']}, "
        f"not_found={stats['not_found']}, "
        f"duplicates={stats['duplicates']}, "
        f"rate_limited={stats['rate_limited']}, "
        f"request_errors={stats['request_errors']}, "
        f"server_errors={stats['server_errors']}, "
        f"other_errors={stats['other_errors']}"
    )


def main() -> int:
    load_env()
    args = parse_args()

    if not args.token:
        print("Missing Eventbrite token. Set EVENTBRITE_OAUTH_TOKEN or pass --token.", file=sys.stderr)
        return 1
    if "{event_id}" not in args.endpoint_template:
        print("--endpoint-template must contain {event_id}.", file=sys.stderr)
        return 1

    state = load_state(args.state_file)
    request_timestamps = deque(float(value) for value in state.get("request_timestamps", []))
    saved_event_ids = {str(value) for value in state.get("saved_event_ids", [])}
    next_allowed_at = time.time()

    session = requests.Session()
    headers = build_headers(args.token)

    try:
        while True:
            if args.max_requests and state["stats"]["attempted"] >= args.max_requests:
                print(f"Reached max request budget: {args.max_requests}")
                break
            if args.target_successes and state["stats"]["successful"] >= args.target_successes:
                print(f"Reached target successes: {args.target_successes}")
                break

            next_allowed_at = wait_until_limit_resets(request_timestamps, next_allowed_at)
            event_id = build_random_event_id(args.prefix, args.min_event_id, args.max_event_id)
            url = args.endpoint_template.format(event_id=event_id)

            try:
                response = session.get(url, headers=headers, timeout=args.timeout)
            except requests.RequestException as error:
                state["stats"]["attempted"] += 1
                state["stats"]["request_errors"] += 1
                state["last_request_at"] = utc_now()
                request_timestamps.append(time.time())
                print(f"Request error for event {event_id}: {error}")
                save_state(args.state_file, state, request_timestamps, saved_event_ids)
                continue

            state["stats"]["attempted"] += 1
            state["last_request_at"] = utc_now()
            request_timestamps.append(time.time())

            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError:
                    state["stats"]["other_errors"] += 1
                    print(f"Received non-JSON response for event {event_id}.")
                else:
                    if handle_success(args.output, saved_event_ids, args.endpoint_template, event_id, payload):
                        state["stats"]["successful"] += 1
                        print(f"Saved event {event_id}")
                    else:
                        state["stats"]["duplicates"] += 1
                        print(f"Duplicate event {event_id} skipped")
            elif response.status_code == 404:
                state["stats"]["not_found"] += 1
            elif response.status_code == 429:
                state["stats"]["rate_limited"] += 1
                retry_after = float(response.headers.get("Retry-After", 1))
                next_allowed_at = max(next_allowed_at, time.time() + retry_after)
                print(f"Rate limited on event {event_id}; backing off for {retry_after:.2f}s")
            elif response.status_code in {401, 403}:
                print(
                    f"Authentication or permission error ({response.status_code}) for event {event_id}: "
                    f"{response.text[:300]}",
                    file=sys.stderr,
                )
                save_state(args.state_file, state, request_timestamps, saved_event_ids)
                return 1
            elif 500 <= response.status_code < 600:
                state["stats"]["server_errors"] += 1
                backoff_seconds = min(30.0, 2.0)
                next_allowed_at = max(next_allowed_at, time.time() + backoff_seconds)
                print(f"Server error {response.status_code} on event {event_id}; retrying after {backoff_seconds:.2f}s")
            else:
                state["stats"]["other_errors"] += 1
                print(f"Unhandled status {response.status_code} for event {event_id}: {response.text[:300]}")

            if args.progress_every and state["stats"]["attempted"] % args.progress_every == 0:
                print_summary(state)

            save_state(args.state_file, state, request_timestamps, saved_event_ids)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        save_state(args.state_file, state, request_timestamps, saved_event_ids)
        print_summary(state)
        session.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())