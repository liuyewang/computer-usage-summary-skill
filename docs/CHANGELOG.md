# Public Changelog

This is a privacy-safe product and validation log. It records decisions and
feedback themes, never ActivityWatch events, window titles, URLs, account
names, local paths, or behavioral telemetry.

## 2026-07-27 - v0.2.2 Review Fixes

- Convert invalid IANA time-zone input into a clean CLI validation error.
- Document the direct `tzdata` install command required by the mirrored skill package.

## 2026-07-26 - v0.2.0 Launch And Validation Setup

### Shipped

- Released local project, category, client, billable-time, weekly, monthly,
  and custom-range reports in v0.2.0.
- Published a bilingual GitHub Pages landing page with a fully synthetic report
  preview and no analytics, tracking pixel, or email form.
- Opened GitHub Discussions for design partners, use cases, and feature votes.

### Decision

- Keep the free core local, open source, account-free, and unlimited.
- Do not add payment, cloud sync, team monitoring, advertising, or activity
  telemetry during validation.

### Next Validation Question

Which private report is used repeatedly enough to justify a paid local Pro
trial: client timesheets, personal weekly reviews, or long-term app trends?

See [VALIDATION_SCORECARD.md](VALIDATION_SCORECARD.md) for the evidence gate.

## 2026-07-27 - v0.2.1 Cross-Platform Packaging

### Shipped

- Moved the real skill directory to the repository-root `skills/` layout so
  Codex and community skill registries can discover the same package.
- Removed the symlink-based compatibility layer and updated installation,
  test, CI, and local marketplace paths.
