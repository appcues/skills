---
name: analytics-query
description: Use when asked for ad-hoc counts of users or events, activity or usage trends over time, top events, NPS results, or a dump/export of raw events from an Appcues account. Answers one-off analytics questions by querying the analytics API.
---

# Appcues analytics query

Answer an analytics question by POSTing a query spec (a JSON document) to
the account's analytics API. The spec's shape decides the result:
`metrics` + `dimensions` present means computed aggregates; `columns`
present means raw event rows. Read-only: this skill only queries, it
never creates, publishes, or deletes anything.

## Getting the data

Use whichever Appcues access you have, in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. Always pass `-o json`.

   ```bash
   appcues status                                  # verify credentials before querying
   appcues analytics query --spec q.json -o json   # sync: prints a bare rows array
   appcues analytics query --spec - -o json        # same, spec on stdin
   appcues analytics query --spec q.json --async -o json   # returns {job_id, status}
   appcues jobs download <JOB_ID> --out result.json # wait, download the result, print the path
   appcues jobs wait <JOB_ID> --timeout 15m -o json # block until done | failed
   appcues jobs get <JOB_ID> -o json                # single status poll
   ```

2. **The Appcues MCP server's equivalent analytics tools**, when there
   is no shell or no binary.

3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort: `POST /v2/accounts/{account_id}/analytics/query` (sync),
   `POST /v2/accounts/{account_id}/analytics/exports` (async),
   `GET /v2/accounts/{account_id}/analytics/exports/{job_id}` (status
   poll). The body is the spec, verbatim.

Pick the first tier available and use it exclusively for the whole
task: this is an availability ladder, not a troubleshooting ladder.
When the CLI is present, every Appcues API interaction goes through it;
never reconstruct a request with curl or raw HTTP because an output
looks wrong or a call failed. Local parsing of results (python3, jq)
is fine.

Whatever the access, verify credentials work before the first query
(`appcues status` on the CLI; any cheap read elsewhere).

## The spec

Fields: `metrics`, `dimensions`, `columns`, `conditions` (a list of
`[field, operator, value]` triples), `order_by`, `start_time`,
`end_time`, `timezone`, `limit`, `offset`, `rank_n`. Each field's
structure, with types and operators, is in `references/spec.md`.

- Never put `account_id` in the spec. It comes from the authenticated
  context; the server ignores any body value.
- Always set an explicit `start_time`/`end_time` matching the window the
  question asks about.
- Nothing validates the spec client-side; the server is the single
  validator (see "Self-correcting on errors" below).

Start from the working examples in `references/` and adapt fields and
dates:

- `references/metrics-by-day.json`: daily users and events; the
  starting point for any "how much activity / usage over time" question.
- `references/top-events.json`: event names ranked by volume; run this
  first when you need to discover what events exist before filtering.
- `references/filtered-metrics.json`: the same daily metrics narrowed
  by a condition triple; the template for "how is flow X / event Y
  doing" questions.
- `references/raw-events.json`: raw event rows via `columns`; use for
  "give me the events themselves" dumps, usually async.

## Sync or async?

- **Sync** (the query route, the CLI default) for bounded, interactive
  questions: aggregates over ranges up to 90 days, or small row samples.
  The 200 body is a bare JSON rows array.
- **Async** (the exports route; `--async` on the CLI) for wide ranges or
  raw event dumps. Sync results are clamped at 1000 rows; the response
  marks the clamp with an `X-Rows-Truncated` header, which the CLI echoes
  as `"rows_truncated":true` on its informational stderr line. Truncated
  numbers are incomplete: rerun the same spec async instead of trusting
  them.

The async flow: submitting returns `{job_id, status: "queued"}`. On
the CLI, one command finishes the job:

```bash
appcues jobs download <JOB_ID> --out result.json
```

It waits for the job, downloads the result to the file, and prints the
local path; the file content is the same bare rows array a sync query
returns, and on `failed` the error carries the `failure_reason`.

Without the CLI, poll the status route until:

- `done`: the response includes a presigned `download_url` valid for
  1 hour (`expires_at` says when). Fetch it with a plain HTTP GET and
  **no auth headers**, capturing the URL programmatically: never by
  copying it from displayed output (some runtimes mask credential-like
  strings in what they display, and a presigned URL contains one). If
  the link has expired, poll again: every poll mints a fresh one.
- `failed`: the response includes a `failure_reason`; report it.

## Self-correcting on errors

Whatever the access path, an invalid spec gets a structured 400 whose
`detail` names the offending field (for example: NPS metrics require a
`flow_id` condition; sync time ranges are capped at 90 days). Read
`detail`, fix the spec it names, and retry. Do not guess or
pre-validate; the error tells you what to change.

On the CLI that failure is loud and structured: non-zero exit, exactly
one JSON line on stderr with the API error body embedded under `body`
(so `detail` is at `body.detail`):

```json
{"error":true,"type":"api","status":400,"message":"API error 400: Bad Request — time range of 147 days exceeds the 90-day maximum for this query shape","body":{"detail":"time range of 147 days exceeds the 90-day maximum for this query shape","status":400,"title":"Bad Request"},"exit_code":4}
```

| exit | meaning | do |
|---|---|---|
| 0 | success | continue |
| 1 | unexpected failure | stop, report the JSON `message` |
| 2 | usage error (bad flags/arguments) | fix the invocation, retry once |
| 3 | missing/bad credentials | stop, report exactly what is needed |
| 4 | API rejected the spec (4xx) | fix the field named in `body.detail`, retry |
| 5 | rate limited / 5xx (already retried) | stop, report |

## Pacing

Responses carry rate-limit state: `X-RateLimit-Limit` / `-Remaining` /
`-Reset` headers on every call, `X-Concurrency-Limit` / `-Used` (the
account's async job slots) on the async routes. The CLI echoes them as
one informational JSON line on stderr, e.g.
`{"rate_limit":{"limit":60,"remaining":41,"reset":1787747700},"rows_truncated":true}`,
keeping stdout data-only, so parse stdout only. When `remaining` gets
low, slow down until the `reset` epoch.

## Answer format (MUST)

Emit exactly this structure: answer first, then the data, then the spec
used, then notes. Keep all four parts, in this order.

```
<one-sentence answer to the question>

## Data
<the rows or a table of them; "no matching data in <range>" if empty>

## Spec used
<the exact spec JSON that produced the data>

## Notes
<truncation, range caps hit, or "none">
```

- If a result is empty, say so in the answer and keep every section;
  never drop one.
- Never present truncated sync rows as totals; note the truncation and
  the async rerun.

## Rules

- Run unattended: never ask the user questions. If credentials are
  missing or a call fails after self-correction, stop and report exactly
  what failed and what is needed, quoting the structured error.
- Credentials are ambient (the environment, or the CLI's own config,
  which the CLI reads itself). Never read, print, or search for
  credential files or secret values; if a call fails with a credentials
  error, stop and report what is missing.
- A failed or odd-looking call is never a reason to switch access
  paths: read the structured error and act on it (see "Self-correcting
  on errors").
- Read-only: queries and exports only.
