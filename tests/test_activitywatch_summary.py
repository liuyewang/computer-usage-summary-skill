import datetime as dt
import importlib.util
import os
import pathlib
import unittest
from unittest import mock
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).parents[1]
SKILL_ROOT = ROOT / "skills" / "computer-usage-summary"
SCRIPT = SKILL_ROOT / "scripts" / "activitywatch_summary.py"
SPEC = importlib.util.spec_from_file_location("activitywatch_summary", SCRIPT)
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)
SOURCE = importlib.import_module("summary_core.source")


class ActivityWatchSummaryTests(unittest.TestCase):
    def setUp(self):
        self.timezone = ZoneInfo("Asia/Singapore")
        self.start = dt.datetime(2026, 8, 3, tzinfo=self.timezone)
        self.end = self.start + dt.timedelta(days=1)

    def test_merge_intervals_removes_duplicate_and_partial_overlap(self):
        intervals = [
            (self.start, self.start + dt.timedelta(hours=10)),
            (self.start, self.start + dt.timedelta(hours=8)),
            (self.start + dt.timedelta(hours=5), self.start + dt.timedelta(hours=12)),
        ]

        merged = SUMMARY.merge_intervals(intervals)

        self.assertEqual(merged, [(self.start, self.start + dt.timedelta(hours=12))])

    def test_summarize_period_deduplicates_afk_and_caps_day_by_union(self):
        afk_events = [
            self.event(self.start, 10 * 3600, {"status": "afk"}),
            self.event(self.start, 10 * 3600, {"status": "afk"}),
            self.event(self.start + dt.timedelta(hours=10), 2 * 3600, {"status": "not-afk"}),
            self.event(self.start + dt.timedelta(hours=10), 2 * 3600, {"status": "not-afk"}),
        ]
        window_events = [
            self.event(
                self.start + dt.timedelta(hours=10),
                2 * 3600,
                {"app": "Google Chrome", "title": "Research - Google Chrome"},
            )
        ]

        result = SUMMARY.summarize_period(
            window_events,
            afk_events,
            self.start,
            self.end,
            self.timezone,
            "Asia/Singapore",
        )

        self.assertEqual(result["active_seconds"], 7200.0)
        self.assertEqual(result["afk_seconds"], 36000.0)
        self.assertEqual(result["coverage_seconds"], 43200.0)
        self.assertLessEqual(result["active_seconds"] + result["afk_seconds"], 86400.0)

    def test_summarize_period_displays_local_timezone(self):
        afk_events = [self.event(self.start, 60, {"status": "not-afk"})]
        window_events = [self.event(self.start, 60, {"app": "Code", "title": "project"})]

        result = SUMMARY.summarize_period(
            window_events,
            afk_events,
            self.start,
            self.end,
            self.timezone,
            "Asia/Singapore",
        )

        self.assertEqual(result["timezone"], "Asia/Singapore")
        self.assertEqual(result["range_start"], "2026-08-03T00:00:00+08:00")
        self.assertEqual(result["timeline"][0]["start"], "2026-08-03T00:00:00+08:00")

    def test_system_timezone_takes_precedence_over_tz_environment(self):
        with mock.patch.dict(os.environ, {"TZ": "UTC"}), mock.patch.object(
            SUMMARY.os.path,
            "realpath",
            return_value="/usr/share/zoneinfo/Asia/Singapore",
        ):
            timezone, name = SUMMARY.resolve_timezone()

        self.assertEqual(name, "Asia/Singapore")
        self.assertEqual(str(timezone), "Asia/Singapore")

    def test_dst_fallback_day_is_capped_at_twenty_four_hours(self):
        timezone = ZoneInfo("America/New_York")
        start = dt.datetime(2026, 11, 1, tzinfo=timezone)
        end = dt.datetime(2026, 11, 2, tzinfo=timezone)
        absolute_start = start.astimezone(dt.timezone.utc)
        afk_events = [
            self.event(absolute_start, 13 * 3600, {"status": "not-afk"}),
            self.event(
                absolute_start + dt.timedelta(hours=13),
                12 * 3600,
                {"status": "afk"},
            ),
        ]

        result = SUMMARY.summarize_period(
            [],
            afk_events,
            start,
            end,
            timezone,
            "America/New_York",
        )

        self.assertLessEqual(result["active_seconds"] + result["afk_seconds"], 86400.0)
        self.assertLessEqual(result["coverage_seconds"], 86400.0)

    def test_browser_pages_group_normalized_titles_and_count_sessions(self):
        active_intervals = [(self.start, self.start + dt.timedelta(hours=1))]
        window_events = [
            self.event(
                self.start + dt.timedelta(minutes=1),
                60,
                {"app": "Google Chrome", "title": "Example - Google Chrome - Profile"},
            ),
            self.event(
                self.start + dt.timedelta(minutes=5),
                120,
                {"app": "Google Chrome", "title": "Example - Google Chrome - Profile"},
            ),
        ]

        pages = SUMMARY.aggregate_browser_pages(
            window_events,
            active_intervals,
            self.start,
            self.end,
            self.timezone,
        )

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["title"], "Example")
        self.assertEqual(pages[0]["active_seconds"], 180.0)
        self.assertEqual(pages[0]["foreground_sessions"], 2)
        self.assertEqual(pages[0]["first_seen"], "2026-08-03T00:01:00+08:00")
        self.assertEqual(pages[0]["last_active"], "2026-08-03T00:07:00+08:00")

    def test_default_parser_selects_copyable_markdown_report(self):
        args = SUMMARY.build_parser().parse_args([])

        self.assertEqual(args.format, "markdown")
        self.assertEqual(args.table, "report")

    def test_markdown_report_contains_daily_and_browser_tables(self):
        day = {
            "date": "2026-08-03",
            "timezone": "Asia/Singapore",
            "active_seconds": 180.0,
            "afk_seconds": 60.0,
            "coverage_seconds": 240.0,
            "untracked_seconds": 86160.0,
            "apps": [],
            "browser_pages": [
                {
                    "app": "Google Chrome",
                    "title": "Example",
                    "foreground_sessions": 2,
                    "active_seconds": 180.0,
                    "first_seen": "2026-08-03T10:00:00+08:00",
                    "last_active": "2026-08-03T10:05:00+08:00",
                }
            ],
            "timeline": [],
        }
        summary = {
            "timezone": "Asia/Singapore",
            "range_start": "2026-08-03T00:00:00+08:00",
            "range_end": "2026-08-04T00:00:00+08:00",
            "days": [day],
        }

        report = SUMMARY.render_report(summary, "markdown")

        self.assertIn("Asia/Singapore", report)
        self.assertIn("UTC+08:00", report)
        self.assertIn("| date | active_seconds |", report)
        self.assertIn("| browser | title | foreground_sessions |", report)
        self.assertIn("Google Chrome", report)

    def test_multi_day_summary_preserves_full_range_totals(self):
        end = self.start + dt.timedelta(days=2)
        afk_events = [
            self.event(self.start, 36 * 3600, {"status": "not-afk"}),
            self.event(self.start + dt.timedelta(hours=36), 12 * 3600, {"status": "afk"}),
        ]

        result = SUMMARY.summarize_period(
            [], afk_events, self.start, end, self.timezone, "Asia/Singapore"
        )

        self.assertEqual(result["active_seconds"], 36 * 3600)
        self.assertEqual(result["coverage_seconds"], 48 * 3600)
        self.assertEqual(result["untracked_seconds"], 0.0)

        day = {
            "date": "2026-08-03",
            "active_seconds": 3600.0,
            "afk_seconds": 1800.0,
            "coverage_seconds": 5400.0,
            "untracked_seconds": 8100.0,
            "timezone": "Asia/Singapore",
            "first_seen": "2026-08-03T09:00:00+08:00",
            "last_active": "2026-08-03T11:00:00+08:00",
            "main_focus": "development",
        }
        total = {
            **day,
            "date": "2026-08-03 to 2026-08-04",
            "active_seconds": 7200.0,
            "afk_seconds": 3600.0,
            "coverage_seconds": 10800.0,
            "untracked_seconds": 16200.0,
            "main_focus": "communication",
            "days": [day, {**day, "date": "2026-08-04"}],
        }
        _, rows = SUMMARY.table_data(total, "daily")
        self.assertEqual(rows[-1][0], "TOTAL")
        self.assertEqual(rows[-1][1], 7200.0)

    def test_invalid_browser_threshold_is_rejected(self):
        with self.assertRaises(SystemExit):
            SUMMARY.build_parser().parse_args(["--min-tab-seconds", "nan"])

    def test_activity_categories_and_main_focus_are_deterministic(self):
        afk_events = [self.event(self.start, 120, {"status": "not-afk"})]
        window_events = [
            self.event(self.start, 60, {"app": "Code", "title": "main.py"}),
            self.event(self.start + dt.timedelta(seconds=60), 60, {"app": "微信", "title": "微信 (聊天)"}),
        ]

        result = SUMMARY.summarize_period(
            window_events,
            afk_events,
            self.start,
            self.end,
            self.timezone,
            "Asia/Singapore",
        )

        self.assertEqual(SUMMARY.classify_activity("Code", "main.py")["category"], "development")
        self.assertEqual(SUMMARY.classify_activity("Google Chrome", "新标签页")["confidence"], "unknown context")
        self.assertEqual(result["main_focus"], "development")
        self.assertEqual(result["category_totals"]["development"], 60.0)
        self.assertEqual(result["category_totals"]["communication"], 60.0)

    def test_browser_short_visits_are_summarized(self):
        afk_events = [self.event(self.start, 300, {"status": "not-afk"})]
        window_events = [
            self.event(self.start, 60, {"app": "Google Chrome", "title": "Short - Google Chrome"}),
            self.event(self.start + dt.timedelta(seconds=60), 180, {"app": "Google Chrome", "title": "Long - Google Chrome"}),
        ]

        result = SUMMARY.summarize_period(
            window_events,
            afk_events,
            self.start,
            self.end,
            self.timezone,
            "Asia/Singapore",
        )

        self.assertEqual(result["browser_short_visits"]["count"], 1)
        self.assertEqual(result["browser_short_visits"]["active_seconds"], 60.0)

    def test_unavailable_report_respects_requested_format(self):
        summary = {
            "available": False,
            "reason": "local ActivityWatch server unavailable",
            "source": "ActivityWatch",
            "timezone": "Asia/Singapore",
            "range_start": "2026-08-03T00:00:00+08:00",
            "range_end": "2026-08-04T00:00:00+08:00",
        }

        markdown = SUMMARY.render_table(summary, "markdown", "report")
        tsv = SUMMARY.render_table(summary, "tsv", "apps")

        self.assertIn("unavailable", markdown)
        self.assertIn("local ActivityWatch server unavailable", markdown)
        self.assertIn("status\treason\tsource", tsv)

    def test_latest_activitywatch_buckets_are_selected(self):
        buckets = {
            "old-window": {
                "type": "currentwindow",
                "last_updated": "2026-10-21T07:29:42.701000+00:00",
            },
            "new-window": {
                "type": "currentwindow",
                "last_updated": "2026-11-10T11:00:37.655000+00:00",
            },
            "old-afk": {
                "type": "afkstatus",
                "last_updated": "2026-10-21T07:29:41.821000+00:00",
            },
            "new-afk": {
                "type": "afkstatus",
                "last_updated": "2026-11-10T11:05:14.177000+00:00",
            },
        }
        with mock.patch.object(
            SOURCE,
            "get_json",
            side_effect=[
                buckets,
                [{"timestamp": "2026-11-10T10:00:00+00:00", "duration": 1, "data": {}}],
                [{"timestamp": "2026-11-10T10:00:00+00:00", "duration": 1, "data": {"status": "not-afk"}}],
            ],
        ) as get_json:
            window_events, afk_events = SOURCE.fetch_events(
                self.start,
                self.end,
            )

        self.assertEqual(len(window_events), 1)
        self.assertEqual(len(afk_events), 1)
        self.assertIn("/buckets/new-window/events?", get_json.call_args_list[1].args[0])
        self.assertIn("/buckets/new-afk/events?", get_json.call_args_list[2].args[0])

    def test_empty_activitywatch_events_are_unavailable(self):
        buckets = {
            "window": {"type": "currentwindow", "last_updated": "2026-11-10T11:00:00+00:00"},
            "afk": {"type": "afkstatus", "last_updated": "2026-11-10T11:00:00+00:00"},
        }
        with mock.patch.object(
            SOURCE, "get_json", side_effect=[buckets, [], []]
        ), self.assertRaisesRegex(SOURCE.ActivityWatchUnavailable, "no events"):
            SOURCE.fetch_events(self.start, self.end)

    @staticmethod
    def event(start, duration, data):
        return {"timestamp": start.astimezone(dt.timezone.utc).isoformat(), "duration": duration, "data": data}


if __name__ == "__main__":
    unittest.main()
