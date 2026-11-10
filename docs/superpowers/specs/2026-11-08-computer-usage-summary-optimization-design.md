# Computer Usage Summary Optimization Design

## Intent

Improve the reliability and usefulness of the local ActivityWatch reporting
skill while preserving its local-only privacy model and existing command-line
entrypoint. The work combines an internal modular refactor with deterministic
activity classification and richer daily/browser summaries.

## Goals

- Split data access, interval math, classification, report shaping, rendering,
  and CLI orchestration into focused modules.
- Keep `scripts/activitywatch_summary.py` executable with the existing command
  names and options.
- Correctly aggregate multi-day ranges without applying a one-day cap to the
  full-range total.
- Add deterministic activity categories and a best-supported daily focus.
- Add a readable “What you did” category summary to the default report.
- Report foreground browser pages above the default threshold and summarize
  omitted short visits without exposing URLs.
- Preserve JSON/Markdown/TSV/CSV output and add fields without removing the
  existing fields.
- Keep all classification local, rule-based, explainable, and dependency-free.

## Non-goals

- No browser extension, browser history, cloud sync, telemetry, or external AI
  inference.
- No process-launch inference or reconstruction of untracked time.
- No automatic installation or repair of ActivityWatch.
- No breaking rename of the existing script or CLI options.
- No new runtime dependency beyond the existing `tzdata` support package.

## Anti-goals

- Do not infer a precise user intention from a generic title.
- Do not turn an observation span into continuous work time.
- Do not classify sensitive titles by uploading or persisting raw activity data.
- Do not hide short browser visits as if they never occurred; summarize them as
  omitted foreground observations.

## Approaches

1. Keep the current 567-line script and add more conditionals. This is the
   smallest immediate diff but makes output, interval math, and future reports
   harder to test independently.
2. Split the script into pure domain modules with a thin compatibility wrapper.
   This is the selected approach because the existing behavior is already
   testable through pure functions and the new features need separate review
   boundaries.
3. Replace the script with a third-party reporting framework. Rejected because
   it adds runtime dependencies, weakens local/privacy control, and does not
   solve the ActivityWatch-specific interval semantics.

## Architecture

The skill package will use a small standard-library-only Python package under
`skills/computer-usage-summary/scripts/summary_core/`. The distinct package
name avoids import ambiguity with the executable `activitywatch_summary.py`:

- `models.py`: typed, JSON-serializable report records and default values.
- `intervals.py`: clipping, deduplication, overlap, session counts, and
  daily-period bounds.
- `source.py`: loopback ActivityWatch API access and source errors.
- `classify.py`: deterministic app/title classification and focus selection.
- `reports.py`: period aggregation, browser short-visit accounting, and report
  shaping.
- `render.py`: JSON, Markdown, TSV, and CSV output.
- `cli.py`: argument parsing, validation, source orchestration, and file output.
- `__init__.py`: stable import surface for tests and the wrapper.

`activitywatch_summary.py` remains the executable compatibility wrapper and
delegates to `summary_core.cli.main`. Existing public helper names
used by the test suite will remain available through the package import
surface or a documented compatibility re-export.

## Product behavior

### Deterministic categories

Each observed foreground record receives one category from a fixed ordered
rule set such as `development`, `communication`, `research`, `email`,
`creative`, `system`, or `other`. Matching uses application names and already
sanitized titles. Unknown matches remain `other` with `unknown context` rather
than a fabricated explanation.

### Daily focus

The daily overview will expose `main_focus`, chosen from the category with the
largest accumulated active time. Ties resolve by category order, then app name.
The report will show the top category duration and top supporting apps.

### Browser short visits

The default human report will show pages with at least 120 accumulated
foreground seconds. It will add a short-visit summary containing the omitted
row count and total foreground seconds. `--min-tab-seconds` continues to
override the threshold for table output, and JSON retains the complete grouped
data plus the summary metadata.

### Unavailable source

When ActivityWatch cannot be queried, every requested output format will use a
structured unavailable result. Markdown will include the reason and caveats;
TSV/CSV will contain status, reason, and source columns; JSON will preserve the
machine-readable error object.

## Compatibility and privacy

- Existing CLI options and output fields remain supported.
- New fields are additive and documented in README and the skill instructions.
- All timestamps remain local-time ISO strings with explicit offsets.
- URL-like titles continue to become `[URL omitted]` before classification or
  rendering.
- Raw events stay in memory and are never sent outside `127.0.0.1`.

## Verification gates

- Existing tests pass before refactor and after each migration step.
- New tests cover multi-day totals, unavailable output formats, category rules,
  focus ties, browser short visits, invalid thresholds, and CLI compatibility.
- Python 3.9 and 3.12 syntax/behavior remains supported on macOS, Windows, and
  Linux CI.
- Plugin validation, compile checks, full unit tests, and a synthetic end-to-
  end report run pass before release.

## Review focus

- A two-day range must not be capped at 24 hours while a one-day DST fallback
  range remains bounded.
- A generic browser title must not become a confident activity claim.
- A short browser visit must be counted in the omitted summary, not silently
  discarded.
- A missing ActivityWatch bucket must produce format-appropriate unavailable
  output without a traceback.
- A malformed threshold or timezone must produce a clean CLI validation error.
