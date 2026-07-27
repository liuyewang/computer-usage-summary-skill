# Contributing

Issues and pull requests are welcome. Keep the project local-first and
dependency-free at runtime.

Before opening a pull request, run:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m py_compile skills/computer-usage-summary/scripts/activitywatch_summary.py
python3 -m unittest discover -s tests -v
```

When changing the plugin manifest or package structure, also run the Codex
plugin validator:

```bash
python3 /path/to/codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Do not add real ActivityWatch databases, window titles, browsing history, or
other personal activity records to fixtures, issues, or pull requests.
