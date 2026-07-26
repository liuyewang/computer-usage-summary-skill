# Computer Usage Summary Skill

A privacy-first [Codex Agent Skill](https://github.com/openai/skills) for
summarizing local macOS activity from [ActivityWatch](https://activitywatch.net/).
It reports foreground application time, observed foreground sessions, AFK time,
and a sanitized window-title timeline. All data stays on the Mac.

中文简介：这是一个基于本机 ActivityWatch 的 macOS 使用情况汇总技能。它不会上传
活动数据，不安装浏览器扩展，也不会展示完整网址。

## Requirements

- macOS
- Python 3.9 or newer
- ActivityWatch running locally with the window and AFK watchers enabled

Install ActivityWatch from an official source of your choice. Before enabling
automatic startup, verify its code signature and macOS Gatekeeper status. This
repository never downloads, installs, or starts ActivityWatch automatically.

## Install In Codex

Install the `skills/computer-usage-summary` directory from this repository
using Codex's skill installer, then restart Codex. For a local clone, copy that
directory into `~/.codex/skills/computer-usage-summary/`.

After this repository is published, a GitHub-directory install looks like:

```text
$skill-installer install https://github.com/<owner>/computer-usage-summary-skill/tree/main/skills/computer-usage-summary
```

## Usage

Ask Codex: `Summarize what I did today on my Mac.`

Or run the bundled script directly:

```bash
# Default JSON report for an agent or another program
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today

# Paste an application table into Excel, Numbers, or Feishu Sheets
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --format tsv --table apps

# A readable timeline in Markdown
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --date today --format markdown --table timeline

# An Excel-friendly CSV file with a UTF-8 BOM
python3 skills/computer-usage-summary/scripts/activitywatch_summary.py --start 2026-07-20 --end 2026-07-26 --format csv --table apps --csv-bom --output weekly-apps.csv
```

Tables are available as `summary`, `apps`, and `timeline`. User-facing times
are emitted in the selected local time zone; use `--timezone Asia/Singapore`
to make a report reproducible across machines.

## Limitations

Accurate historical foreground and AFK time begins only after ActivityWatch
starts recording. Without ActivityWatch, macOS has no reliable public history
for foreground-app time or application launches. The skill can provide a
clearly labeled limited-evidence report but will not invent time totals.

See [PRIVACY.md](PRIVACY.md) for the data-handling rules and
[CONTRIBUTING.md](CONTRIBUTING.md) for development checks.

## License

[MIT](LICENSE)

