---
name: account-inventory
description: Use when asked what's in an Appcues account, for an inventory, overview, or content audit. Reports everything that exists in the account, flows with their published state, segments, and tags, with counts.
---

# Appcues account inventory

Produce a single report of the account's contents: flows (split by
published state), segments, and tags.

## Getting the data

You need three listings: **flows**, **segments**, and **tags**. Use
whichever Appcues access you have, in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH:

   ```bash
   appcues flows list -o json
   appcues segments list -o json
   appcues tags list -o json
   ```

   On failure the CLI exits non-zero and prints one JSON line to stderr,
   e.g. `{"error":true,"type":"auth","status":401,"message":"...","exit_code":3}`.
   Exit code 3 means missing or bad credentials: stop and report exactly
   what is needed. Any other non-zero exit: stop and report the JSON
   `message`.

2. **The Appcues MCP server's equivalent list tools**, when there is no
   shell or no binary.

3. **The [API v2](https://api.appcues.com) directly** as a last resort.

The report only needs each item's `id`, `name`, and (for flows)
`published`.

## Report format (MUST)

Emit exactly this structure: same summary line, same sections, same
order, same headings. Do not regroup items thematically, add sections,
or drop the summary line.

```
Account <id>: <n> flows (<n> published), <n> segments, <n> tags

## Flows
Published (<n>):
- <name> (<id>)
Unpublished (<n>):
- <name> (<id>)

## Segments
- <name> (<id>)

## Tags
- <name> (<id>)
```

- Sort every list alphabetically by name, case-insensitive.
- If a listing is empty, keep the section and say so ("no segments"),
  never omit it.

## Rules

- Read-only: never create, publish, unpublish, or delete anything.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails, stop and report exactly what failed and what
  is needed, quoting the CLI's JSON error line or the MCP/API error
  message.
- Pick the first access tier available and use it exclusively for the
  whole task; a failed or odd-looking call is never a reason to switch
  to a lower tier.
- Credentials are ambient (the environment, or the CLI's own config,
  which the CLI reads itself). Never read, print, or search for
  credential files or secret values.
