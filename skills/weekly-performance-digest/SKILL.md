---
name: weekly-performance-digest
description: Use when asked how Appcues flows performed or are doing this week, for a weekly or N-day digest, a performance report or summary, what changed this week, top movers, or how flows are doing now vs the previous period. Produces a period-over-period performance digest of the account's published flows.
---

# Appcues weekly performance digest

Report how the account's published flows performed over the last period
(default 7 days) compared to the same-length period immediately before:
totals, top movers, and completion-rate regressions. Read-only: this
skill only reads listings and analytics, it never creates, publishes,
or deletes anything.

## Getting the data

The digest needs one dataset: per published flow, the counts `shown`,
`completed`, `skipped`, `errors`, `unique_users` and the completion
rate, for the current period and the previous same-length period. Use
whichever Appcues access you have, in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. One command returns the whole dataset:

   ```bash
   appcues flows +digest --days 7 -o json
   ```

   `--days` accepts 1–90; use 7 unless the request names another window.

2. **The Appcues MCP server's equivalent tools** (flow listings plus
   analytics/performance queries), when there is no shell or no binary.

3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort.

Pick the first tier available and use it exclusively for the whole
task: this is an availability ladder, not a troubleshooting ladder.
When the CLI is present, every Appcues API interaction goes through it;
never reconstruct a request with curl or raw HTTP because an output
looks wrong or a call failed. Local parsing of results (python3, jq)
is fine.

Credentials are ambient (the environment, or the CLI's own config,
which the CLI reads itself). Never read, print, or search for
credential files or secret values; on an auth failure, stop and report
what is missing.

### The digest envelope (CLI tier)

`flows +digest -o json` prints one JSON object:

```json
{
  "period":          {"start_time": "...", "end_time": "..."},
  "previous_period": {"start_time": "...", "end_time": "..."},
  "flows": [
    {
      "flow_id": "...", "name": "...",
      "shown": 0, "completed": 0, "skipped": 0, "errors": 0,
      "unique_users": 0, "completion_rate": 0.0,
      "previous": { "shown": 0, "completed": 0, "skipped": 0,
                    "errors": 0, "unique_users": 0,
                    "completion_rate": 0.0 },
      "deltas": { "shown_pct": 0.0, "completion_rate_pts": 0.0,
                  "unique_users_pct": 0.0 }
    }
  ]
}
```

- `flows` holds published flows only, already sorted by
  `completion_rate` descending.
- `completion_rate` is `completed / shown` as a percent, one decimal;
  it is `null` when `shown` is 0.
- Every `deltas` field is `null` when the previous period has no
  baseline (previous value 0). A `null` delta means "new or previously
  inactive", never "no change".
- The CLI may print one informational JSON line to stderr (rate-limit
  state, `"rows_truncated":true`). Parse stdout only, but if
  `rows_truncated` appears, say so in the report's data notes: the
  digest was computed from an incomplete row set.

### Without the composite command (MCP / raw API tiers)

Compose the same dataset from three reads:

1. List flows (`GET /v2/accounts/{account_id}/flows`); keep only
   `published: true`.
2. Run this analytics query for the current period
   (`POST /v2/accounts/{account_id}/analytics/query`):

   ```json
   {
     "metrics": ["events", "users"],
     "dimensions": ["flow_id", "name"],
     "conditions": [["name", "in", ["appcues:flow_started",
       "appcues:flow_completed", "appcues:flow_skipped",
       "appcues:step_error"]]],
     "start_time": "<period start, RFC 3339 UTC>",
     "end_time": "<period end, RFC 3339 UTC>"
   }
   ```

3. Run the identical query again with the window shifted to the
   same-length period immediately before (previous end = current
   start).

Then fold the rows per `flow_id`: `appcues:flow_started` events →
`shown` (its `users` value → `unique_users`), `appcues:flow_completed`
→ `completed`, `appcues:flow_skipped` → `skipped`, `appcues:step_error`
→ `errors`. Completion rate = completed/shown. A flow absent from the
rows had zero activity, not missing data. Do not put `account_id` in
the spec body; it comes from the authenticated context.

## Branching on CLI failure

The CLI fails loud and structured: non-zero exit, exactly one JSON line
on stderr, e.g.
`{"error":true,"type":"auth","status":401,"message":"...","exit_code":3}`.

| exit | meaning | do |
|---|---|---|
| 0 | success | continue |
| 1 | unexpected failure | stop, report the JSON `message` |
| 2 | usage error (bad flags/arguments) | fix the invocation, retry once |
| 3 | missing/bad credentials | stop, report exactly what is needed |
| 4 | API rejected the request (4xx) | stop, report status + `message` |
| 5 | rate limited / 5xx (already retried) | stop, report |

A failed or odd-looking call is never a reason to switch access tiers:
read the structured error and act on it.

## Report format (MUST)

Emit exactly this structure: same sections, same order, same headings.
Do not regroup sections, rename them, or drop the summary line. State
empty sections; never omit them.

```
Appcues weekly digest — <n> published flows, <period start date> → <period end date> (vs the previous <days> days)

## Summary
<one or two sentences: total shown and completed across all flows with
their % change vs the previous period, and how many flows moved up vs
down>

## Top movers — up
- <name> (<flow_id>): shown <n> (<+x.x%>), completion <r.r%> (<±p.p pts>)

## Top movers — down
- <name> (<flow_id>): shown <n> (<-x.x%>), completion <r.r%> (<±p.p pts>)

## Degraded completion
- <name> (<flow_id>): <r.r%>, was <r.r%> (<-p.p pts>), shown <n>

## All published flows
| name | shown | completed | completion % | Δ rate pts | unique users |
|---|---|---|---|---|---|

## Period & data notes
- Current period: <start_time> → <end_time>; previous: <start_time> → <end_time>.
- No previous-period baseline (deltas are null): <flow names, or "none">.
- Data caveats: <"rows truncated — digest computed from an incomplete row set" when the truncation marker appeared, otherwise "none">.
```

- **Top movers — up**: flows with `deltas.shown_pct` > 0, sorted by
  `shown_pct` descending, at most 5. Empty: "no flows up".
- **Top movers — down**: flows with `deltas.shown_pct` < 0, sorted by
  `shown_pct` ascending, at most 5. Empty: "no flows down".
- Flows with a `null` `shown_pct` never appear in either movers list;
  they go in the no-baseline line of Period & data notes.
- **Degraded completion**: flows with `deltas.completion_rate_pts`
  ≤ -5.0, sorted ascending (worst regression first). Empty: "no flows
  with completion down 5+ pts".
- **All published flows**: every flow from the dataset, in its given
  order (completion rate descending); render `null` rates and deltas
  as `—`. Empty: "no published flows".
- Dates in the heading line are the date parts of the period bounds;
  full timestamps belong in Period & data notes.

## Rules

- Read-only: never create, publish, unpublish, or delete anything.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails, stop and report exactly what failed and what
  is needed, quoting the structured error line, not prose.
- Default to a 7-day window; use another length only when the request
  names one. The previous period is always derived (same length,
  immediately before), never asked for.
