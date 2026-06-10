#!/usr/bin/env python3
"""Build an iCalendar file from data/matches.csv."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_INPUT = Path("data/matches.csv")
DEFAULT_OUTPUT = Path("dist/world-cup-2026.ics")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate World Cup 2026 .ics calendar")
    parser.add_argument("--input", default=DEFAULT_INPUT, type=Path)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--calendar-name", default="Mundial 2026")
    parser.add_argument("--alarm-minutes", default=30, type=int)
    return parser.parse_args()


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold_line(line: str) -> list[str]:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return [line]

    lines = []
    current = ""
    for char in line:
        candidate = current + char
        prefix = " " if lines else ""
        if len((prefix + candidate).encode("utf-8")) > 75:
            lines.append((" " if lines else "") + current)
            current = char
        else:
            current = candidate
    if current:
        lines.append((" " if lines else "") + current)
    return lines


def append(lines: list[str], line: str) -> None:
    lines.extend(fold_line(line))


def event_summary(row: dict) -> str:
    matchup = row.get("matchup", "").strip()
    if matchup:
        return f"Mundial 2026: {matchup}"
    return f"Mundial 2026: {row.get('event_name', 'Partido')}"


def event_location(row: dict) -> str:
    parts = [row.get("venue", ""), row.get("city", ""), row.get("country", "")]
    return ", ".join(part for part in parts if part)


def event_description(row: dict) -> str:
    details = []
    location = event_location(row)
    if location:
        details.append(f"Sede: {location}")
    if row.get("broadcasts"):
        details.append(f"Transmision: {row['broadcasts']}")
    if row.get("source_url"):
        details.append(f"Fuente: {row['source_url']}")
    details.append("Calendario sujeto a cambios.")
    return "\n".join(details)


def build_calendar(rows: list[dict], calendar_name: str, alarm_minutes: int) -> str:
    now = format_utc(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//Calendario Mundial//World Cup 2026//ES",
    ]
    append(lines, f"X-WR-CALNAME:{escape_text(calendar_name)}")
    append(lines, "X-WR-TIMEZONE:UTC")

    for row in rows:
        start = parse_utc(row["start_utc"])
        duration = int(row.get("duration_minutes") or 120)
        end = start + timedelta(minutes=duration)
        uid = f"world-cup-2026-{row['id']}@calendario-mundial.local"

        lines.append("BEGIN:VEVENT")
        append(lines, f"UID:{uid}")
        append(lines, f"DTSTAMP:{now}")
        append(lines, f"DTSTART:{format_utc(start)}")
        append(lines, f"DTEND:{format_utc(end)}")
        append(lines, f"SUMMARY:{escape_text(event_summary(row))}")
        append(lines, f"DESCRIPTION:{escape_text(event_description(row))}")
        location = event_location(row)
        if location:
            append(lines, f"LOCATION:{escape_text(location)}")
        append(lines, "STATUS:CONFIRMED")
        append(lines, "TRANSP:OPAQUE")
        if alarm_minutes > 0:
            lines.append("BEGIN:VALARM")
            append(lines, f"TRIGGER:-PT{alarm_minutes}M")
            append(lines, "ACTION:DISPLAY")
            append(lines, f"DESCRIPTION:{escape_text(event_summary(row))}")
            lines.append("END:VALARM")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main() -> int:
    args = parse_args()
    with args.input.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise SystemExit(f"No rows found in {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        build_calendar(rows, args.calendar_name, args.alarm_minutes),
        encoding="utf-8",
        newline="",
    )
    print(f"Wrote {len(rows)} events to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
