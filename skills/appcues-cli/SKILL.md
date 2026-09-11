---
name: appcues-cli
description: Use when asked to run, set up, check, or troubleshoot the appcues CLI, verify credentials or connection status, manage config profiles, list or inspect flows, experiences, checklists, segments, tags, users, or groups, publish or unpublish content, discover or call an account tool, run an analytics export, or do any other ad hoc Appcues task that no packaged report covers. Not for producing a formatted report or digest; a report request has its own skill.
---

# Driving the appcues CLI

Do one ad hoc Appcues task the way the CLI expects: one command, JSON
out, a plain result back. This skill produces no report; it describes
how to operate the tool.

## Access

Use whichever Appcues access you have, in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. Always pass `-o json`. Anything without a typed command is
   reachable as `appcues tools call <name>`; tool names are identical
   on the CLI and the MCP server, so name a tool once for both.
2. **The Appcues MCP server's equivalent tools**, when there is no shell
   or no binary. Every typed command below has a same-named tool; the
   command map still tells you which one to reach for.
3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort.

Pick the first tier available and use it exclusively for the whole
task. A failed or odd-looking call is never a reason to drop to a lower
tier: read the structured error and act on it.

## First: confirm the connection

```bash
appcues status
```

Prints the account ID, the API host, and whether the credentials work.
Run it before anything else when the user asks about setup, when the
first real command fails with exit 3, or when it is unclear which
account is active. `appcues profiles list` shows the saved profiles with
credentials truncated; `--profile <name>` or `APPCUES_PROFILE` selects
one, `--account <id>` overrides the profile's account for one call.

## Command map

Every command takes `-o json`; `--dry-run` prints write requests instead
of sending them (reads still run). Check flags with
`appcues <command> <subcommand> --help` rather than guessing.

| Need | Command |
|---|---|
| Flows | `flows list`, `flows get <id>`, `flows publish <id>`, `flows unpublish <id>` |
| Experiences (pins, mobile, launchpads, banners, flows 2.0, embeds, NPS) | `experiences list <type>`, `experiences get`, `experiences publish`, `experiences unpublish` |
| Checklists | `checklists list`, `checklists get`, `checklists publish`, `checklists unpublish` |
| Tags | `tags list`, `tags get <id>` |
| Segments | `segments list`, `segments get`, `segments create`, `segments update`, `segments delete`, `segments add-users`, `segments remove-users` |
| Users | `users get <id>`, `users update --attr k=v`, `users events <id>`, `users track`, `users delete` |
| Groups | `groups get <id>`, `groups update --attr k=v`, `groups add-users` |
| Screenshots of a draft | `screenshots <flow-or-experience-id>` (writes a ZIP) |
| Analytics | `analytics query --spec <file>` (sync by default; async returns a job) |
| Export jobs | `jobs get <id>`, `jobs wait <id>`, `jobs download <id>` (waits, downloads, prints the local path) |
| Anything else | `tools list`, `tools describe <name>`, `tools call <name> --input '<json>'` (or `--attr k=v`, repeatable) |

Two habits that keep this safe and cheap:

- **Writes: dry-run first.** Publish, unpublish, create, update, delete,
  add-users, remove-users, track: run once with `--dry-run`, check the
  printed request, then run for real. Skip the rehearsal only when the
  user explicitly asked for a single direct run.
- **Exports: never copy download URLs.** `jobs download` fetches the
  result itself. A presigned URL relayed through a transcript is masked
  and comes out corrupted.

When no typed command fits, discover before calling: `tools list -o json`
shows what this API key can reach, `tools describe <name>` gives the
input schema. Prefer `tools call` over raw API requests.

## When a command fails

The CLI exits non-zero and prints exactly one JSON line on stderr:

```json
{"error":true,"type":"auth","status":401,"message":"...","exit_code":3}
```

| exit | `type` | meaning | do |
|---|---|---|---|
| 1 | `unexpected` | unknown failure | stop, report the message |
| 2 | `usage` | bad flags or arguments | fix the invocation (check `--help`), retry once |
| 3 | `config`, `auth` | missing or bad credentials | stop, report exactly what is needed |
| 4 | `api`, `tool` | API rejected the request (4xx), or a tool ran and reported failure (envelope under `body`) | stop, report status and message |
| 5 | `rate_limited`, `server` | transient 429/5xx, already retried | stop, report |

Data goes to stdout and everything else to stderr, so JSON output is
always parseable even on failure.

## Reporting back

Say what you ran and what came back, in this order: the command, the
outcome in one line, then the data the user asked for (trimmed to the
fields that matter, unless they asked for raw JSON). On failure quote the
JSON error line verbatim and state what would fix it, as data (the
missing variable or profile field name), not prose.

## Rules

- Run unattended: never ask the user a question. If credentials are
  missing or a call fails, stop and report what failed and what is
  needed.
- Credentials are ambient (the environment, or the CLI's own config,
  which the CLI reads itself). Never read, print, or search for
  credential files, config files, or secret values. `profiles list` is
  the only sanctioned view of a profile, and it truncates.
- Never run a destructive command (`delete`, `unpublish`, `remove-users`)
  the user did not name. Read-only unless asked to write.
- Stay on one access tier for the whole task.
