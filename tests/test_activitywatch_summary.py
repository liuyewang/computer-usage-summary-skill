import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "computer-usage-summary" / "scripts" / "activitywatch_summary.py"
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

    def test_collects_active_time_sessions_and_local_times(self):
        result = self.collect()
        apps = {item["app"]: item for item in result["apps"]}
        self.assertTrue(result["available"])
        self.assertEqual(result["timezone"], "Asia/Singapore")
        self.assertEqual(result["active_seconds"], 540.0)
        self.assertEqual(result["afk_seconds"], 120.0)
        self.assertEqual(apps["=Spreadsheet"]["foreground_sessions"], 1)
        self.assertEqual(apps["=Spreadsheet"]["active_seconds"], 240.0)
        self.assertEqual(apps["=Spreadsheet"]["first_seen"], "2026-01-02T00:00:00+08:00")
        self.assertEqual(apps["Chat"]["last_active"], "2026-01-02T00:17:00+08:00")

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
        skill = (ROOT / "skills" / "computer-usage-summary" / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: computer-usage-summary\n"))
        self.assertIn("description:", skill.split("---", 2)[1])


if __name__ == "__main__":
    unittest.main()
