# Computer Usage Summary Optimization Checkpoint

## Goal

Implement the approved architecture refactor and deterministic reporting
features from the optimization design while preserving the existing CLI and
privacy model.

## Scope

- Refactor the report script into focused standard-library-only modules.
- Fix multi-day aggregation and unavailable-source output.
- Add deterministic categories, daily focus, and browser short-visit metadata.
- Keep existing CLI options and output fields compatible.
- Update tests and user/developer documentation.

## Current state

- Design: `docs/superpowers/specs/2026-11-08-computer-usage-summary-optimization-design.md`
- Baseline branch: `main`, clean before the design/checkpoint files.
- Baseline tests: 8/8 passed with `.venv/bin/python -m unittest discover -s tests -v`.
- Final tests: 15/15 passed with `.venv/bin/python -m unittest discover -s tests -v`.
- Final compile/static checks: `compileall`, Ruff, and `git diff --check` pass.
- Live CLI verification selects the current `MacBookPro` buckets and returns
  non-zero totals; an older stopped device had previously been selected first.
- The multi-day table now includes a `TOTAL` row; JSON retains full-range
  totals and complete grouped browser data.

## Decisions

- Use package name `summary_core` to avoid collision with the executable module.
- Use deterministic, local rules only; no runtime AI or new runtime dependency.
- Preserve `activitywatch_summary.py` as the stable executable and test import
  surface through compatibility re-exports.
- Do not push or publish external releases in this implementation pass unless
  separately requested.

## Next steps

1. Review the final diff and decide whether to commit this implementation.
2. If explicitly requested, push the branch and handle external platform
   resubmission as a separate publishing workflow.

## Evidence and remaining work

- Evidence is from the baseline test run on 2026-11-10 in Asia/Singapore.
- Production code, tests, workflow, and user-facing documentation are updated
  and committed in the source repository.
- The local Codex plugin validator is not installed; manifest JSON and package
  layout were checked manually instead.
- Source repository commits `154523a` and `a66278c` are pushed; `origin/main`
  matches `a66278c` and the worktree is clean.
- Awesome Codex Plugins PR #693 is open with all checks passing, including the
  centralized scanner threshold and generated marketplace sync; maintainer
  merge is still pending.
- ClawHub version `0.3.0` was submitted under `@liuyewang/computer-usage-summary`,
  but its owner-visible publication state is `checks_failed` with
  `clawscan` and `trufflehog` failed and automatic retrying. It is not claimed
  as publicly released.
- HOL Registry and SkillsMP are expected to follow the generator-backed Awesome
  listing after PR #693 merges. skills.sh is source-indexed from GitHub; its
  authenticated API could not be queried here. LobeHub and Cursor Directory
  were not resubmitted to avoid duplicate entries.
