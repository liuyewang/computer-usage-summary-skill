# Contributing

Issues and pull requests are welcome. Keep the project local-first and
dependency-free at runtime.

Before opening a pull request, run:

```bash
python3 -m py_compile plugins/computer-usage-summary-skill/skills/computer-usage-summary/scripts/activitywatch_summary.py
python3 -m unittest discover -s tests -v
```

Do not add real ActivityWatch databases, window titles, browsing history, or
other personal activity records to fixtures, issues, or pull requests.
