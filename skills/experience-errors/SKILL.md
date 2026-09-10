---
name: experience-errors
description: Use when asked which Appcues flows, experiences, or steps are erroring, what the error messages are, whether errors went up or spiked today or this week, for a daily error check or error monitoring report, or which browsers the errors happen in. Reports error-rate spikes per experience plus step errors grouped by flow, step, and error message, compared to the previous period.
---

# Appcues experience errors

Report the account's experience errors over the last period (default 7
days, `1` for a daily check): which experiences are spiking in error
rate, and every step error grouped by flow, step, and error message,
each compared to the same-length period immediately before. Read-only:
this skill only queries, it never creates, publishes, or deletes
anything.

This skill is written to be run on a schedule by whatever runtime hosts
it (a cron, an agent scheduler). The skill itself never schedules, waits,
or keeps state between runs: every run is one read plus one report.

## Getting the data

The report needs one dataset: error counts (`events`) and affected users
(`users`) per `flow_id`, `step_id`, and error message, for the current
period and the previous one. Use whichever Appcues access you have, in
this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. First the spike detector from the account tools (the MCP tool
   set, callable from the CLI); it compares each experience's error
   rate over the recent days against its own history, which catches a
   regression that raw counts hide when traffic changes:

   ```bash
   appcues status                                                        # verify credentials
   appcues tools call list_issue_spikes -o json                          # flagged experiences, or "No issue spikes detected."
   appcues tools call list_experience_issues --attr experience_id=<ID> -o json   # once per flagged experience: recent messages
   ```

   If `list_issue_spikes` fails with exit 5 and a body saying MCP server
   access is not available for this account, or exit 3 because the
   environment has no tools service, the "Spiking experiences" section
   reads "account tools unavailable" and the rest of the report is
   built from analytics alone; decide that once, up front.

   Then the counts by message, one command per error event family:
   classic flows report `appcues:step_error` and
   `appcues:step_child_error`, Flows 2.0 experiences report
   `appcues:v2:step_error` (grouped by `experience_id` instead of
   `flow_id`). Run all three; an empty result for some is normal.

   ```bash
   appcues analytics +compare --spec references/step-errors.json --days 7 -o json
   appcues analytics +compare --spec references/step-child-errors.json --days 7 -o json
   appcues analytics +compare --spec references/v2-step-errors.json --days 7 -o json
   ```

   `--days` accepts 1–90; use 7 unless the request names another window,
   and 1 for "today vs yesterday" checks. The spec paths are relative to
   this skill's directory. The spec's own `start_time`/`end_time` are
   ignored: the CLI sets both windows.

   For "which browsers" questions add a fourth call, in addition to the
   three above, with `references/errors-by-browser.json`; it feeds only
   the "By browser" report section.

2. **The Appcues MCP server's tools** `list_issue_spikes` and
   `list_experience_issues` (per flagged `experience_id`) for the spike
   section, plus its analytics query tool for the counts by message,
   when there is no shell or no binary.

3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort: `POST /v2/accounts/{account_id}/analytics/query` with the spec
   body, once per window. There is no spike detector on this tier; the
   section reads "account tools unavailable".

Pick the first tier available and use it exclusively for the whole task:
this is an availability ladder, not a troubleshooting ladder. When the
CLI is present, every Appcues API interaction goes through it; never
reconstruct a request with curl or raw HTTP because an output looks wrong
or a call failed. Local parsing of results (python3, jq) is fine.

Credentials are ambient (the environment, or the CLI's own config, which
the CLI reads itself). Never read, print, or search for credential files
or secret values; on an auth failure, stop and report what is missing.

### The compare envelope (CLI tier)

`analytics +compare -o json` prints one JSON object:

```json
{
  "period":          {"start_time": "...", "end_time": "..."},
  "previous_period": {"start_time": "...", "end_time": "..."},
  "metrics": ["events", "users"],
  "rows": [
    {
      "flow_id": "...", "step_id": "...", "step_error_message": "...",
      "current":  {"events": 0, "users": 0},
      "previous": {"events": 0, "users": 0},
      "deltas":   {"events_pct": 0.0, "users_pct": 0.0}
    }
  ]
}
```

- `rows` is the union of both windows, sorted by `current.events`
  descending. A row present in only one window has zeros in the other.
- The row id is `flow_id` for the two classic specs and `experience_id`
  for the Flows 2.0 spec. Before merging, normalize both to one `id`
  field and remember which kind it is; the report's `flow` column shows
  the name resolved for that id (see "Naming flows").
- A `null` delta means the previous value was 0: a **new** error, never
  "no change". A `-100.0` delta means the error stopped.
- The CLI may print one informational JSON line to stderr (rate-limit
  state, `"rows_truncated":true`). Parse stdout only; if
  `rows_truncated` appears, say so in the data notes.

### Without the composite command (MCP / raw API tiers)

Run each reference spec twice with explicit `start_time`/`end_time`:
the last N days ending now, and the N days before that (previous end =
current start). Join the two row sets on `flow_id` + `step_id` + the
message column, treat a missing row as zero, and compute
`(current - previous) / previous * 100` per metric (null when previous
is 0). Do not put `account_id` in the spec body.

### Naming flows

Ids alone are hard to read. When the report has rows, list flows once
(`appcues flows list -o json`) and Flows 2.0 experiences once
(`appcues experiences list flows-v2 -o json`), or the equivalent
listing tools, and map ids to names. If a listing fails, keep the ids
and note it. In the report, "flow" means the flow or the experience.

## Self-correcting on errors

The server is the only validator. A 400 names the offending field in
`detail` (on the CLI, `body.detail` in the one-line stderr JSON): fix
that field and retry once. The dimension names in the reference specs
come from the analytics engine's vocabulary; if the server rejects one,
the error says so.

| exit | meaning | do |
|---|---|---|
| 0 | success | continue |
| 1 | unexpected failure | stop, report the JSON `message` |
| 2 | usage error | fix the invocation, retry once |
| 3 | missing/bad credentials | stop, report exactly what is needed |
| 4 | API rejected the spec (4xx) | fix the field named in `body.detail`, retry once |
| 5 | rate limited / 5xx (already retried) | stop, report |

## Report format (MUST)

Emit exactly this structure: same sections, same order, same headings.
State empty sections; never omit them. Merge the rows from all three
error specs into one list before building the sections; the message
column is `step_error_message` or `step_child_error_message` depending
on the spec.

```
Appcues experience errors — <total current errors> errors across <n> flows, <s> spiking, <period start date> → <period end date> (vs the previous <days> days: <total previous>, <±x.x%>)

## Verdict
<one sentence: "errors up/down/flat vs previous period", how many experiences are spiking, and whether any new error messages appeared>

## Spiking experiences (error rate)
- <experience name> (<id>, <type>): error rate <r.r%> over the last <n> days vs <b.b%> before — <errors> errors on <shows> shows; latest message: "<message>"

## New errors (no previous baseline)
- <flow name> (<flow_id>) step <step_id>: "<message>" — <n> errors, <u> users

## Rising errors
- <flow name> (<flow_id>) step <step_id>: "<message>" — <n> errors (<+x.x%>), <u> users

## Resolved errors
- <flow name> (<flow_id>) step <step_id>: "<message>" — was <n>, now 0

## All errors
| flow | step_id | message | errors | prev | Δ % | users |
|---|---|---|---|---|---|---|

## By browser
| flow | browser | platform | errors | prev | Δ % | users |
|---|---|---|---|---|---|---|

## Period & data notes
- Current period: <start_time> → <end_time>; previous: <start_time> → <end_time>.
- Data caveats: <"rows truncated — computed from an incomplete row set" when the truncation marker appeared, otherwise "none">.
```

- **Spiking experiences**: every experience `list_issue_spikes`
  flagged, in its order, with the most recent message from
  `list_experience_issues` for that id (or "no recent message"). Tool
  not run: "account tools unavailable". Run and nothing flagged: "no
  spikes detected".
- **New errors**: rows with `deltas.events_pct` null and `current.events`
  > 0, sorted by `current.events` descending. Empty: "no new errors".
- **Rising errors**: rows with `deltas.events_pct` ≥ 50.0 and
  `current.events` ≥ 5, sorted by `events_pct` descending. Empty: "no
  errors up 50%+". The 50% / 5-event floor keeps one-off noise out of
  a daily check; use the request's threshold if it names one.
- **Resolved errors**: rows with `current.events` = 0, sorted by
  `previous.events` descending. Empty: "no errors resolved".
- **All errors**: every row, in the envelope's order; render null deltas
  as `new`. Empty: "no step errors in either period".
- **By browser**: rows from the browser spec, in the envelope's order,
  only when that query was run; render an empty browser as `unknown`.
  Not run: "not requested". Run and empty: "no errors in either period".
- Truncate messages longer than 120 characters with `…`.

## Rules

- Read-only: never create, publish, unpublish, or delete anything.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails after one self-correction, stop and report
  exactly what failed, quoting the structured error line.
- Default to a 7-day window; the previous period is always derived,
  never asked for. Scheduling and alert delivery belong to the runtime
  that invokes this skill, not to the skill.
