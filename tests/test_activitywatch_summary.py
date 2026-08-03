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
        with (
            mock.patch.dict(os.environ, {"TZ": "UTC"}),
            mock.patch.object(
                SUMMARY.os.path,
                "realpath",
                return_value="/usr/share/zoneinfo/Asia/Singapore",
            ),
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

    @staticmethod
    def event(start, duration, data):
        return {"timestamp": start.astimezone(dt.timezone.utc).isoformat(), "duration": duration, "data": data}


if __name__ == "__main__":
    unittest.main()
