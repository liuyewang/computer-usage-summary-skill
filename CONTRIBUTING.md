# Contributing

Issues and pull requests are welcome. Keep the project local-first and
dependency-free at runtime.

Before opening a pull request, run:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m py_compile skills/computer-usage-summary/scripts/activitywatch_summary.py \
  skills/computer-usage-summary/scripts/summary_core/*.py \
  tests/test_activitywatch_summary.py
python3 -m unittest discover -s tests -v
```

When available, run the repository's static checks as well:

```bash
ruff check skills/computer-usage-summary/scripts tests
git diff --check
```

When changing the plugin manifest or package structure, also run the Codex
plugin validator if it is installed in the local environment:

```bash
python3 /path/to/codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Do not add real ActivityWatch databases, window titles, browsing history, or
other personal activity records to fixtures, issues, or pull requests.
