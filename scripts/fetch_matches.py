#!/usr/bin/env python3
"""Fetch and normalize FIFA World Cup 2026 matches from ESPN."""

from __future__ import annotations

import csv
import json
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/"
    "scoreboard?dates=20260611-20260719&limit=200"
)
OUTPUT = Path("data/matches.csv")


def fetch_json(url: str, *, verify_ssl: bool = True) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "calendario-mundial/1.0"})
    context = None if verify_ssl else ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
        return json.load(response)


def team_name(competitor: dict) -> str:
    team = competitor.get("team") or {}
    return team.get("displayName") or team.get("shortDisplayName") or team.get("name") or ""


def event_url(event: dict) -> str:
    for link in event.get("links", []):
        rel = set(link.get("rel", []))
        if "desktop" in rel and "event" in rel:
            return link.get("href", "")
    return ""


def normalize_event(event: dict) -> dict:
    competition = (event.get("competitions") or [{}])[0]
    venue = competition.get("venue") or {}
    address = venue.get("address") or {}
    competitors = competition.get("competitors") or []

    home = ""
    away = ""
    for competitor in competitors:
        if competitor.get("homeAway") == "home":
            home = team_name(competitor)
        elif competitor.get("homeAway") == "away":
            away = team_name(competitor)

    matchup = f"{home} vs {away}" if home and away else event.get("name", "")
    broadcasts = []
    for item in competition.get("broadcasts", []):
        broadcasts.extend(item.get("names", []))

    return {
        "id": event.get("id", ""),
        "start_utc": event.get("date", ""),
        "duration_minutes": "120",
        "home": home,
        "away": away,
        "matchup": matchup,
        "event_name": event.get("name", ""),
        "short_name": event.get("shortName", ""),
        "venue": venue.get("fullName", ""),
        "city": address.get("city", ""),
        "country": address.get("country", ""),
        "broadcasts": ", ".join(dict.fromkeys(broadcasts)),
        "source_url": event_url(event),
    }


def main() -> int:
    try:
        data = fetch_json(API_URL)
    except urllib.error.URLError as error:
        if "CERTIFICATE_VERIFY_FAILED" not in str(error):
            raise
        print(
            "SSL certificate verification failed; retrying without verification. "
            "Install Python certificates to avoid this fallback.",
            file=sys.stderr,
        )
        data = fetch_json(API_URL, verify_ssl=False)
    events = data.get("events", [])
    if not events:
        print("No events found in ESPN response.", file=sys.stderr)
        return 1

    rows = [normalize_event(event) for event in events]
    rows.sort(key=lambda row: (row["start_utc"], row["id"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} matches to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
