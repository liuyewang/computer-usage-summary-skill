# Privacy

This skill reads ActivityWatch only through its local API at `127.0.0.1`.
It does not upload, sync, export, or share activity data unless the user
explicitly asks to save an output file.

The default report includes sanitized window titles after removing URLs and
truncating long text. Titles can still contain sensitive context. Use the
`apps` or `daily` table when titles are unnecessary, and review timeline or
browser-page output before sharing it.

The skill does not install browser extensions, enable `aw-sync`, parse private
Screen Time databases, or infer historical usage from process uptime or macOS
system logs.

The script uses only ActivityWatch's local loopback API at `127.0.0.1:5600`.
Browser reporting covers foreground window titles only. It does not read
browser history, background tabs, synced browser data, or complete URLs.

The project landing page has no analytics script, tracking pixel, or email
form. Design-partner conversations happen through GitHub Discussions and must
not include raw ActivityWatch exports, titles, URLs, account names, or local
paths.
