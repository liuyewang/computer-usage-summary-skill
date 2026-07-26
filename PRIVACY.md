# Privacy

This skill reads ActivityWatch only through its local API at `127.0.0.1`.
It does not upload, sync, export, or share activity data unless the user
explicitly asks to save an output file.

The default timeline includes window titles after removing URLs and truncating
long text. Window titles can still contain sensitive context. Use the `apps`
or `summary` table when titles are unnecessary, and review a `timeline` export
before sharing it. Add `--hide-titles` to export a timeline without titles.

The skill does not install browser extensions, enable `aw-sync`, parse private
Screen Time databases, or infer historical usage from process uptime or macOS
system logs.

The optional `--api-url` is intended for a local loopback ActivityWatch server.
Do not point it at a public or shared endpoint unless the user explicitly
understands the data exposure and network-security implications.

## Local Rules And Reports

The optional `--rules` JSON file maps application names and sanitized titles to
projects, clients, categories, and billable status. It is read from the local
path supplied by the user and is never sent to this project, GitHub, or a third
party. Rules are applied only after URL removal and title truncation.

The project landing page has no analytics script, tracking pixel, or email
form. Design-partner conversations happen through GitHub Discussions and must
not include raw ActivityWatch exports, titles, URLs, account names, or local
paths.
