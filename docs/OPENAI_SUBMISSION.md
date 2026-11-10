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

Current skills-only submission notes. Computer Usage Summary converts local
ActivityWatch records into daily app, AFK, deterministic category, sanitized
timeline, and foreground browser-page reports. The current workflow targets
macOS. It does not require an account, browser extension, cloud sync,
telemetry, or a network service beyond the user's local ActivityWatch API.
URL-like titles are removed before classification and rendering.

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
| Request the category table. | Returns deterministic category totals, top supporting applications, and a stable `main_focus` value without claiming unsupported intent. |
| Export an app report as TSV. | Produces paste-ready columns and escapes spreadsheet formula-like cells. |
| Request a browser table with the default threshold. | Shows grouped foreground pages at or above 120 accumulated seconds and summarizes shorter visits separately. |
| Request a multi-day JSON report. | Preserves the full-range totals while keeping each local day bounded independently. |

## Negative Test Cases

| Prompt or scenario | Expected safe behavior |
| --- | --- |
| Request a historical report when the local ActivityWatch API is unavailable. | Marks duration and session fields unavailable with a structured local-source reason; does not invent totals. |
| Request a report when the required ActivityWatch buckets are missing. | Returns an unavailable result identifying the missing local source. |
| Provide a negative, infinite, or NaN browser threshold. | Rejects the argument with a clean CLI validation error before querying local data. |

## Reviewer Notes

- Upload the generated skills-only package from `skills/`; it contains the final
  installable plugin tree only.
- The repository's tests and fixtures are separate from the uploaded plugin
  tree so reviewers can inspect them without installing test-only content.
- The plugin has no credentials, account flows, MCP tools, UI, or external
  endpoint. Its default API endpoint is `http://127.0.0.1:5600/api/0`.
- The executable wrapper delegates to the standard-library-only
  `scripts/summary_core/` package; the test suite remains outside the installable
  skill tree.
