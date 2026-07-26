# OpenAI Plugin Submission Notes

This document is the reviewer-ready source for a **skills-only** submission to
the OpenAI Plugins Directory. It contains no user activity data.

## Listing

| Field | Value |
| --- | --- |
| Plugin name | Computer Usage Summary |
| Publisher | liuyewang (individual identity; verify in the OpenAI Platform before submission) |
| Category | Productivity |
| Short description | Private local ActivityWatch summaries |
| Website | https://liuyewang.github.io/computer-usage-summary-skill/ |
| Support | https://github.com/liuyewang/computer-usage-summary-skill/blob/main/SUPPORT.md |
| Privacy policy | https://github.com/liuyewang/computer-usage-summary-skill/blob/main/PRIVACY.md |
| Terms | https://github.com/liuyewang/computer-usage-summary-skill/blob/main/LICENSE |
| Availability | Global |
| Authentication | None |
| MCP server | None |

## Release Notes

Initial public skills-only submission. Computer Usage Summary converts local
ActivityWatch records into app, AFK, project, category, billable-time, and
sanitized timeline reports. It supports macOS, Windows, and Linux. The plugin
does not require an account, browser extension, cloud sync, telemetry, or a
network service beyond the user's local ActivityWatch API. URLs are removed
before reports are created.

## Starter Prompts

1. Summarize what I did on my computer today.
2. Create a paste-ready table of my app usage this week.
3. Show a private timeline of my local computer activity.

## Positive Test Cases

Use the repository's fixed synthetic ActivityWatch sample and run
`python3 -m unittest discover -s tests -v` before submission. The test suite
does not connect to a real ActivityWatch instance.

| Prompt or scenario | Expected behavior |
| --- | --- |
| Summarize local activity for one day with ActivityWatch running. | Returns confirmed active and AFK totals plus foreground-app sessions from the local API. |
| Create a weekly project report with a local rules JSON file. | Maps sanitized app/title context to project, client, category, and billable totals; first rule wins. |
| Export an app report as TSV. | Produces paste-ready columns and escapes spreadsheet formula-like cells. |
| Export a timeline as CSV with `--csv-bom --hide-titles`. | Produces a UTF-8-BOM CSV and replaces every title with `[Title hidden]`. |
| Request the monthly app-trend report. | Produces local-date trend rows with active, AFK, and billable time. |

## Negative Test Cases

| Prompt or scenario | Expected safe behavior |
| --- | --- |
| Request a historical report when the local ActivityWatch API is unavailable. | Marks duration and session fields unavailable with a structured local-source reason; does not invent totals. |
| Request a report when the required ActivityWatch buckets are missing. | Returns an unavailable result identifying the missing local source. |
| Provide malformed local attribution rules. | Rejects the rules configuration without exporting, uploading, or changing user data. |

## Reviewer Notes

- Upload the generated skills-only ZIP from `dist/`; it contains the final
  installable plugin tree only.
- The repository's tests and fixtures are separate from the uploaded plugin
  tree so reviewers can inspect them without installing test-only content.
- The plugin has no credentials, account flows, MCP tools, UI, or external
  endpoint. Its default API endpoint is `http://127.0.0.1:5600/api/0`.
