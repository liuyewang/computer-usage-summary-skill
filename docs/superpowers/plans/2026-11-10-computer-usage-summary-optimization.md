# Computer Usage Summary Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the local ActivityWatch reporting skill into focused modules and add deterministic activity, focus, and browser-visit summaries without breaking the existing CLI.

**Architecture:** Keep `skills/computer-usage-summary/scripts/activitywatch_summary.py` as a thin executable and compatibility import surface. Move interval math, source access, classification, report shaping, rendering, and CLI orchestration into the standard-library-only `scripts/summary_core/` package.

**Tech Stack:** Python 3.9+, `datetime`, `zoneinfo`, `argparse`, `urllib`, `csv`, `json`, `unittest`; no new runtime dependency.

**Spec:** `docs/superpowers/specs/2026-11-08-computer-usage-summary-optimization-design.md`

## Global Constraints

- Keep all ActivityWatch access on `http://127.0.0.1:5600/api/0`.
- Preserve existing CLI options: `--date`, `--start`, `--end`, `--timezone`, `--format`, `--table`, `--min-tab-seconds`, and `--output`.
- Preserve existing report fields; new fields are additive.
- Never emit complete URLs; classify only sanitized titles.
- Keep one-day active/away/coverage totals bounded by the actual local day and 24 hours.
- Do not cap a multi-day aggregate total at 24 hours.

## Review Focus

- Multi-day totals must include all requested days while daily DST fallback totals remain bounded.
- A generic title must remain `other` / `unknown context` rather than becoming a confident activity claim.
- Browser pages below the default threshold must be represented in short-visit metadata.
- Missing buckets or a stopped local service must produce format-appropriate unavailable output.
- Invalid timezone and threshold values must produce clean CLI errors.

### Task 1: Establish RED tests and compatibility contracts

**Files:**
- Modify: `tests/test_activitywatch_summary.py`
- Test: `tests/test_activitywatch_summary.py`

- [x] **Step 1: Add failing tests** for multi-day totals, format-aware unavailable output, invalid finite thresholds, category/focus output, and browser short-visit metadata.
- [x] **Step 2: Run the focused tests** and confirm they fail for the current implementation for the intended reasons.
- [x] **Step 3: Commit is not required yet; keep the RED changes in the working tree for the implementation tasks.**

### Task 2: Extract models, interval math, and source access

**Files:**
- Create: `skills/computer-usage-summary/scripts/summary_core/__init__.py`
- Create: `skills/computer-usage-summary/scripts/summary_core/models.py`
- Create: `skills/computer-usage-summary/scripts/summary_core/intervals.py`
- Create: `skills/computer-usage-summary/scripts/summary_core/source.py`
- Modify: `skills/computer-usage-summary/scripts/activitywatch_summary.py`
- Test: `tests/test_activitywatch_summary.py`

- [x] **Step 1: Move pure interval and event normalization functions** into `summary_core/intervals.py` without changing their observable results.
- [x] **Step 2: Move loopback API access and source error handling** into `summary_core/source.py`.
- [x] **Step 3: Add model/default helpers** needed by unavailable and report paths.
- [x] **Step 4: Re-export compatibility names** from the executable wrapper.
- [x] **Step 5: Run the full unit suite and compile check; confirm all existing tests pass.**

### Task 3: Add deterministic classification and focus summaries

**Files:**
- Create: `skills/computer-usage-summary/scripts/summary_core/classify.py`
- Modify: `skills/computer-usage-summary/scripts/summary_core/models.py`
- Modify: `tests/test_activitywatch_summary.py`

- [x] **Step 1: Add focused tests** for category precedence, generic-title fallback, deterministic tie-breaking, and main-focus duration.
- [x] **Step 2: Run the new tests and verify RED.**
- [x] **Step 3: Implement ordered local rules** over app names and sanitized titles only.
- [x] **Step 4: Add category totals, top supporting apps, and `main_focus` to daily summaries.**
- [x] **Step 5: Run the full suite and inspect JSON for additive fields.**

### Task 4: Add browser short-visit and multi-day aggregation behavior

**Files:**
- Modify: `skills/computer-usage-summary/scripts/summary_core/intervals.py`
- Create or modify: `skills/computer-usage-summary/scripts/summary_core/reports.py`
- Modify: `tests/test_activitywatch_summary.py`

- [x] **Step 1: Add the multi-day and short-visit regression tests if not already covered by Task 1.**
- [x] **Step 2: Run them and confirm the pre-fix failures.**
- [x] **Step 3: Apply the 24-hour cap only to a single local calendar day; preserve absolute duration for multi-day aggregates.**
- [x] **Step 4: Keep complete browser groups in structured data and calculate omitted count/seconds for the display threshold.**
- [x] **Step 5: Run the full suite and a synthetic two-day JSON report.**

### Task 5: Extract rendering/CLI and handle unavailable output

**Files:**
- Create: `skills/computer-usage-summary/scripts/summary_core/render.py`
- Create: `skills/computer-usage-summary/scripts/summary_core/cli.py`
- Modify: `skills/computer-usage-summary/scripts/activitywatch_summary.py`
- Modify: `tests/test_activitywatch_summary.py`

- [x] **Step 1: Add tests** for Markdown, TSV, CSV, JSON, and unavailable output shape plus invalid thresholds.
- [x] **Step 2: Run them and verify RED.**
- [x] **Step 3: Move parser and rendering orchestration** into the package, preserving the wrapper entrypoint.
- [x] **Step 4: Render unavailable results according to the requested format and add the report caveats section.**
- [x] **Step 5: Run the full suite, compile checks, and CLI help.**

### Task 6: Update user-facing documentation and review the skill contract

**Files:**
- Modify: `skills/computer-usage-summary/SKILL.md`
- Modify: `README.md`
- Modify: `docs/OPENAI_SUBMISSION.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `CONTRIBUTING.md`

- [x] **Step 1: Update the skill instructions** for categories, focus, short visits, and unavailable formats while preserving privacy constraints.
- [x] **Step 2: Correct stale submission examples** so every documented CLI option exists.
- [x] **Step 3: Document the module layout and test commands.**
- [x] **Step 4: Add a changelog entry for the optimization.**
- [x] **Step 5: Run documentation searches for stale flags and version claims.**

### Task 7: Final verification and review

**Files:**
- Review: all changed files

- [x] **Step 1: Run `.venv/bin/python -m unittest discover -s tests -v`.**
- [x] **Step 2: Run `py_compile` for every Python file under the skill scripts and tests.**
- [x] **Step 3: Run plugin/skill validation available in the local environment.** No local validator was installed; manifest/package checks were performed manually.
- [x] **Step 4: Run synthetic end-to-end commands for Markdown, JSON, TSV, CSV, and multi-day output; unavailable source paths are covered by focused source/render tests.**
- [x] **Step 5: Inspect `git diff --check`, `git status`, and the complete diff for privacy, compatibility, and scope.**
- [x] **Step 6: Report actual verification evidence and remaining external work; do not push or publish without explicit request.**
