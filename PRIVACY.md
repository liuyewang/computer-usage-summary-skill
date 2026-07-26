# Privacy

This skill reads ActivityWatch only through its local API at `127.0.0.1`.
It does not upload, sync, export, or share activity data unless the user
explicitly asks to save an output file.

The default timeline includes window titles after removing URLs and truncating
long text. Window titles can still contain sensitive context. Use the `apps`
or `summary` table when titles are unnecessary, and review a `timeline` export
before sharing it.

The skill does not install browser extensions, enable `aw-sync`, parse private
Screen Time databases, or infer historical usage from process uptime or macOS
system logs.

