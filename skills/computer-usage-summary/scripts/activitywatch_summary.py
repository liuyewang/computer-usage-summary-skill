#!/usr/bin/env python3
"""Summarize local ActivityWatch window and AFK events without external access."""

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from zoneinfo import ZoneInfo

DEFAULT_API = "http://127.0.0.1:5600/api/0"
URL_PATTERN = re.compile(r"(?:https?://|www\.|\b[\w.-]+\.(?:com|net|org|cn|io|app|dev)\b)", re.I)
MAX_TITLE_LENGTH = 160


class ActivityWatchUnavailable(RuntimeError):
    """Raised when accurate local ActivityWatch data cannot be retrieved."""


def get_json(path, api=DEFAULT_API):
    with urllib.request.urlopen(f"{api}{path}", timeout=5) as response:
        return json.load(response)


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(value):
    return max(0.0, value.total_seconds())


def overlap(start, end, intervals):
    return sum(seconds(min(end, right) - max(start, left)) for left, right in intervals if left < end and right > start)


def resolve_timezone(value):
    if value:
        return ZoneInfo(value)
    return dt.datetime.now().astimezone().tzinfo


def timezone_name(timezone):
    return getattr(timezone, "key", None) or str(timezone)


def local_iso(value, timezone):
    return parse_time(value).astimezone(timezone).isoformat()


def safe_title(title):
    title = " ".join((title or "").split())
    return "[URL omitted]" if URL_PATTERN.search(title) else title[:MAX_TITLE_LENGTH]


def format_duration(value):
    total = int(round(value))
    hours, remainder = divmod(total, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds_value:02}"


def safe_cell(value):
    """Prevent spreadsheet formula evaluation when a cell is pasted or imported."""
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def collect_summary(start_day, end_day, timezone, fetch=get_json, include_titles=True):
    start = dt.datetime.combine(start_day, dt.time.min, timezone).astimezone(dt.timezone.utc)
    end = dt.datetime.combine(end_day + dt.timedelta(days=1), dt.time.min, timezone).astimezone(dt.timezone.utc)
    query = urllib.parse.urlencode({"starttime": start.isoformat(), "endtime": end.isoformat()})
    try:
        buckets = fetch("/buckets/")
        window_id = next(key for key, value in buckets.items() if value.get("type") == "currentwindow")
        afk_id = next(key for key, value in buckets.items() if value.get("type") == "afkstatus")
        window_events = fetch(f"/buckets/{urllib.parse.quote(window_id, safe='')}/events?{query}")
        afk_events = fetch(f"/buckets/{urllib.parse.quote(afk_id, safe='')}/events?{query}")
    except (OSError, StopIteration, ValueError, urllib.error.URLError) as error:
        raise ActivityWatchUnavailable(f"ActivityWatch data is unavailable: {error}") from error
    if not window_events:
        raise ActivityWatchUnavailable("ActivityWatch has no window events for the requested range.")

    active_intervals = []
    afk_seconds = 0.0
    for event in afk_events:
        event_start = max(parse_time(event["timestamp"]), start)
        event_end = min(parse_time(event["timestamp"]) + dt.timedelta(seconds=event.get("duration", 0)), end)
        if event_end <= event_start:
            continue
        if event.get("data", {}).get("status") == "not-afk":
            active_intervals.append((event_start, event_end))
        else:
            afk_seconds += seconds(event_end - event_start)

    apps = defaultdict(lambda: {"active_seconds": 0.0, "events": [], "first_seen": None, "last_active": None})
    timeline = []
    for event in window_events:
        event_start = max(parse_time(event["timestamp"]), start)
        event_end = min(parse_time(event["timestamp"]) + dt.timedelta(seconds=event.get("duration", 0)), end)
        if event_end <= event_start:
            continue
        active = overlap(event_start, event_end, active_intervals)
        if active <= 0:
            continue
        data = event.get("data", {})
        app = data.get("app") or "Unknown"
        item = apps[app]
        item["active_seconds"] += active
        item["events"].append((event_start, event_end))
        item["first_seen"] = min(item["first_seen"] or event_start, event_start)
        item["last_active"] = max(item["last_active"] or event_end, event_end)
        timeline.append({
            "start": event_start.astimezone(timezone).isoformat(),
            "end": event_end.astimezone(timezone).isoformat(),
            "app": app,
            "title": safe_title(data.get("title", "")) if include_titles else "[Title hidden]",
            "active_seconds": round(active, 1),
        })

    summary_apps = []
    for app, value in apps.items():
        events = sorted(value["events"])
        sessions = 0
        previous_end = None
        for event_start, event_end in events:
            if previous_end is None or event_start - previous_end > dt.timedelta(seconds=5):
                sessions += 1
            previous_end = max(previous_end or event_end, event_end)
        summary_apps.append({
            "app": app,
            "foreground_sessions": sessions,
            "active_seconds": round(value["active_seconds"], 1),
            "first_seen": value["first_seen"].astimezone(timezone).isoformat(),
            "last_active": value["last_active"].astimezone(timezone).isoformat(),
        })

    summary_apps.sort(key=lambda item: item["active_seconds"], reverse=True)
    return {
        "available": True,
        "timezone": timezone_name(timezone),
        "range_start": start.astimezone(timezone).isoformat(),
        "range_end": end.astimezone(timezone).isoformat(),
        "active_seconds": round(sum(item["active_seconds"] for item in summary_apps), 1),
        "afk_seconds": round(afk_seconds, 1),
        "apps": summary_apps,
        "timeline": timeline,
    }


def table_data(summary, table):
    if table == "summary":
        return (
            ["metric", "value"],
            [
                ["range_start", summary["range_start"]],
                ["range_end", summary["range_end"]],
                ["timezone", summary["timezone"]],
                ["active_seconds", summary["active_seconds"]],
                ["active_duration", format_duration(summary["active_seconds"])],
                ["afk_seconds", summary["afk_seconds"]],
                ["afk_duration", format_duration(summary["afk_seconds"])],
                ["source", "ActivityWatch"],
            ],
        )
    if table == "apps":
        return (
            ["app", "foreground_sessions", "active_seconds", "active_duration", "first_seen", "last_active", "source"],
            [[item["app"], item["foreground_sessions"], item["active_seconds"], format_duration(item["active_seconds"]), item["first_seen"], item["last_active"], "ActivityWatch"] for item in summary["apps"]],
        )
    return (
        ["start", "end", "app", "title", "active_seconds", "active_duration", "source"],
        [[item["start"], item["end"], item["app"], item["title"], item["active_seconds"], format_duration(item["active_seconds"]), "ActivityWatch"] for item in sorted(summary["timeline"], key=lambda item: item["start"])],
    )


def unavailable_data(reason):
    return ["status", "reason", "source"], [["unavailable", reason, "ActivityWatch"]]


def render_table(summary, output_format, table, csv_bom=False):
    if output_format == "json":
        return json.dumps(summary, ensure_ascii=False)
    headers, rows = table_data(summary, table) if summary["available"] else unavailable_data(summary["reason"])
    if output_format == "markdown":
        escaped = lambda value: safe_cell(value).replace("|", "\\|").replace("\n", " ")
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines.extend("| " + " | ".join(escaped(value) for value in row) + " |" for row in rows)
        return "\n".join(lines)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t" if output_format == "tsv" else ",", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows([[safe_cell(value) for value in row] for row in rows])
    return ("\ufeff" if output_format == "csv" and csv_bom else "") + buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--date", help="Local date in YYYY-MM-DD format or 'today'")
    group.add_argument("--start", help="Inclusive local start date in YYYY-MM-DD format")
    parser.add_argument("--end", help="Inclusive local end date; required with --start")
    parser.add_argument("--timezone", help="IANA time zone, for example Asia/Singapore; defaults to the local time zone")
    parser.add_argument("--api-url", default=DEFAULT_API, help="Local ActivityWatch API URL; defaults to http://127.0.0.1:5600/api/0")
    parser.add_argument("--format", choices=("json", "markdown", "tsv", "csv"), default="json", help="TSV is suitable for pasting into a spreadsheet")
    parser.add_argument("--table", choices=("summary", "apps", "timeline"), default="apps", help="Table for Markdown, TSV, or CSV output")
    parser.add_argument("--csv-bom", action="store_true", help="Prefix CSV output with a UTF-8 BOM for spreadsheet compatibility")
    parser.add_argument("--hide-titles", action="store_true", help="Replace timeline window titles with [Title hidden]")
    parser.add_argument("--output", help="Optional UTF-8 file path; otherwise write to standard output")
    args = parser.parse_args()
    if args.csv_bom and args.format != "csv":
        parser.error("--csv-bom requires --format csv")

    timezone = resolve_timezone(args.timezone)
    if args.start:
        if not args.end:
            parser.error("--end is required with --start")
        start_day = dt.date.fromisoformat(args.start)
        end_day = dt.date.fromisoformat(args.end)
    else:
        start_day = dt.datetime.now(timezone).date() if args.date in (None, "today") else dt.date.fromisoformat(args.date)
        end_day = start_day
    if end_day < start_day:
        parser.error("--end must not precede --start")

    try:
        fetch = lambda path: get_json(path, args.api_url)
        summary = collect_summary(start_day, end_day, timezone, fetch, include_titles=not args.hide_titles)
    except ActivityWatchUnavailable as error:
        summary = {"available": False, "reason": str(error), "timezone": timezone_name(timezone)}
    result = render_table(summary, args.format, args.table, args.csv_bom)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as file:
            file.write(result)
    else:
        print(result, end="" if result.endswith("\n") else "\n")
    return 0 if summary["available"] else 1


if __name__ == "__main__":
    sys.exit(main())
