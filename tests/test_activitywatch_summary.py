import importlib.util
import json
import sys
import unittest
from contextlib import redirect_stderr
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "computer-usage-summary"
SCRIPT = SKILL_ROOT / "scripts" / "activitywatch_summary.py"
SPEC = importlib.util.spec_from_file_location("activitywatch_summary", SCRIPT)
summary_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(summary_script)


class FixtureFetch:
    def __init__(self, payload):
        self.payload = payload

    def __call__(self, path):
        if path == "/buckets/":
            return self.payload["buckets"]
        if "window" in path:
            return self.payload["window_events"]
        if "afk" in path:
            return self.payload["afk_events"]
        raise AssertionError(path)


class ActivityWatchSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_path = ROOT / "tests" / "fixtures" / "activitywatch_sample.json"
        cls.payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        cls.timezone = ZoneInfo("Asia/Singapore")

    def collect(self):
        return summary_script.collect_summary(
            date(2026, 1, 2),
            date(2026, 1, 2),
            self.timezone,
            FixtureFetch(self.payload),
        )

    def collect_with_rules(self):
        rules_path = ROOT / "tests" / "fixtures" / "rules_sample.json"
        return summary_script.collect_summary(
            date(2026, 1, 2),
            date(2026, 1, 2),
            self.timezone,
            FixtureFetch(self.payload),
            rules=summary_script.load_rules(rules_path),
        )

    def test_collects_active_time_sessions_and_local_times(self):
        result = self.collect()
        apps = {item["app"]: item for item in result["apps"]}
        self.assertTrue(result["available"])
        self.assertEqual(result["timezone"], "Asia/Singapore")
        self.assertEqual(result["active_seconds"], 540.0)
        self.assertEqual(result["billable_seconds"], 0.0)
        self.assertEqual(result["afk_seconds"], 120.0)
        self.assertEqual(apps["=Spreadsheet"]["foreground_sessions"], 1)
        self.assertEqual(apps["=Spreadsheet"]["active_seconds"], 240.0)
        self.assertEqual(apps["=Spreadsheet"]["first_seen"], "2026-01-02T00:00:00+08:00")
        self.assertEqual(apps["Chat"]["last_active"], "2026-01-02T00:17:00+08:00")

    def test_rules_map_sanitized_titles_and_billable_projects(self):
        result = self.collect_with_rules()
        projects = {item["project"]: item for item in result["projects"]}
        categories = {item["category"]: item for item in result["categories"]}
        self.assertEqual(result["billable_seconds"], 240.0)
        self.assertEqual(projects["Quarterly review"]["client"], "Northwind")
        self.assertEqual(projects["Quarterly review"]["billable_seconds"], 240.0)
        self.assertEqual(projects["Internal coordination"]["active_seconds"], 300.0)
        self.assertEqual(categories["Client work"]["active_seconds"], 240.0)
        self.assertFalse(any("private.example.com" in item["title"] for item in result["timeline"]))

    def test_first_matching_rule_wins(self):
        rules = summary_script.load_rules(ROOT / "tests" / "fixtures" / "rules_sample.json")
        attributes = summary_script.attributes_for("=Spreadsheet", "[URL omitted]", rules)
        self.assertEqual(attributes["project"], "Quarterly review")

    def test_invalid_rules_are_rejected(self):
        invalid_path = ROOT / "tests" / "fixtures" / "invalid_rules.json"
        invalid_path.write_text('{"rules": [{"title_pattern": "["}]}', encoding="utf-8")
        self.addCleanup(invalid_path.unlink)
        with self.assertRaises(summary_script.RulesConfigurationError):
            summary_script.load_rules(invalid_path)

    def test_invalid_timezone_is_a_cli_error(self):
        stderr = StringIO()
        with patch.object(sys, "argv", ["activitywatch_summary.py", "--timezone", "Not/AZone"]):
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                summary_script.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unknown IANA time zone: Not/AZone", stderr.getvalue())

    def test_week_and_month_ranges(self):
        week_start, week_end = summary_script.parse_date_range("2026-01-02", None, None, "week", self.timezone)
        month_start, month_end = summary_script.parse_date_range("2026-02-10", None, None, "month", self.timezone)
        self.assertEqual((week_start, week_end), (date(2025, 12, 29), date(2026, 1, 4)))
        self.assertEqual((month_start, month_end), (date(2026, 2, 1), date(2026, 2, 28)))

    def test_report_templates_are_paste_ready(self):
        result = self.collect_with_rules()
        timesheet = summary_script.render_table(result, "tsv", "client-timesheet")
        review = summary_script.render_table(result, "markdown", "weekly-review")
        trend = summary_script.render_table(result, "csv", "app-trend")
        self.assertIn("Northwind\tQuarterly review", timesheet)
        self.assertIn("top_project", review)
        self.assertIn("2026-01-02", trend)

    def test_trend_includes_afk_and_active_time(self):
        result = self.collect_with_rules()
        self.assertEqual(result["trend"], [{
            "date": "2026-01-02",
            "active_seconds": 540.0,
            "afk_seconds": 120.0,
            "billable_seconds": 240.0,
        }])

    def test_sanitizes_urls_and_truncates_titles(self):
        result = self.collect()
        titles = [item["title"] for item in result["timeline"]]
        self.assertIn("[URL omitted]", titles)
        self.assertFalse(any("private.example.com" in title for title in titles))
        self.assertLessEqual(max(map(len, titles)), summary_script.MAX_TITLE_LENGTH)

    def test_can_hide_timeline_titles(self):
        result = summary_script.collect_summary(
            date(2026, 1, 2),
            date(2026, 1, 2),
            self.timezone,
            FixtureFetch(self.payload),
            include_titles=False,
        )
        self.assertEqual({item["title"] for item in result["timeline"]}, {"[Title hidden]"})

    def test_spreadsheet_outputs_escape_formulas(self):
        result = self.collect()
        tsv = summary_script.render_table(result, "tsv", "apps")
        csv_output = summary_script.render_table(result, "csv", "timeline", csv_bom=True)
        self.assertIn("'=Spreadsheet", tsv)
        self.assertTrue(csv_output.startswith("\ufeff"))
        self.assertNotIn("private.example.com", csv_output)

    def test_markdown_escapes_cell_separators(self):
        result = self.collect()
        markdown = summary_script.render_table(result, "markdown", "timeline")
        self.assertIn("Project\\|Plan", markdown)

    def test_missing_buckets_is_unavailable(self):
        with self.assertRaises(summary_script.ActivityWatchUnavailable):
            summary_script.collect_summary(date(2026, 1, 2), date(2026, 1, 2), self.timezone, lambda _: {})

    def test_empty_events_is_unavailable(self):
        payload = dict(self.payload)
        payload["window_events"] = []
        with self.assertRaises(summary_script.ActivityWatchUnavailable):
            summary_script.collect_summary(date(2026, 1, 2), date(2026, 1, 2), self.timezone, FixtureFetch(payload))

    def test_unavailable_tables_are_paste_ready(self):
        unavailable = {"available": False, "reason": "No local server", "timezone": "Asia/Singapore"}
        self.assertEqual(summary_script.render_table(unavailable, "tsv", "apps"), "status\treason\tsource\nunavailable\tNo local server\tActivityWatch\n")
        self.assertIn("| status | reason | source |", summary_script.render_table(unavailable, "markdown", "apps"))

    def test_skill_frontmatter_is_present(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: computer-usage-summary\n"))
        self.assertIn("description:", skill.split("---", 2)[1])


if __name__ == "__main__":
    unittest.main()
