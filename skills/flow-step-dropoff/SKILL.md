---
name: flow-step-dropoff
description: Use when asked where users drop off inside an Appcues flow, which step loses the most users, why a flow's completion rate is low, or for a step-by-step funnel of one flow. Reports per-step started, completed, skipped, and error counts for a single flow.
---

# Appcues flow step drop-off

Explain a flow's completion rate step by step: how many users reached
each step, how many completed or skipped it, and where the largest drop
happens, over the last period (default 7 days). Read-only: this skill
only queries analytics, it never creates, publishes, or deletes
anything.

## Getting the data

One dataset per flow: `events` and `users` per `step_id` and event name
for the flow's lifecycle events. Use whichever Appcues access you have,
in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. Copy `references/step-funnel.json`, replace `<FLOW_ID>` and the
   placeholder dates, then:

   ```bash
   appcues status                                     # verify credentials
   appcues analytics query --spec step-funnel.json -o json
   ```

2. **The Appcues MCP server's equivalent analytics query tool**, when
   there is no shell or no binary.

3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort: `POST /v2/accounts/{account_id}/analytics/query` with the
   spec body.

Pick the first tier available and use it exclusively for the whole task:
this is an availability ladder, not a troubleshooting ladder. When the
CLI is present, every Appcues API interaction goes through it; never
reconstruct a request with curl or raw HTTP because an output looks wrong
or a call failed. Local parsing of results (python3, jq) is fine.

Credentials are ambient (the environment, or the CLI's own config, which
the CLI reads itself). Never read, print, or search for credential files
or secret values; on an auth failure, stop and report what is missing.

### Which flow

Use the flow the request names (by id, or by name via the flows
listing). If it names none, run `appcues flows +digest --days 7 -o json`
(or compose the same from the listing and analytics) and take the
published flow with the lowest non-null `completion_rate` and
`shown` ≥ 20. If no flow reaches 20, take the one with the highest
`shown` above 0 and say so in the data notes. If every published flow
has 0 shown, emit the report skeleton once with the heading line
"Appcues step drop-off — no flow activity in the last 7 days" and every
section set to "no flow activity", then stop. Never ask which, and never
widen the window to find more traffic: low volume is a finding, not a
reason to change the period.

### Step order and labels

The public API exposes no step content: `flows get` returns the flow's
name, published state, and tags only, so do not call it for steps and
do not go looking elsewhere. The funnel rows are the only source: order
steps by `reached` descending (users move through a flow in sequence,
so earlier steps have at least as many users as later ones) and label
each by its `step_id`. `flow_started`/`flow_completed` rows carry an
empty `step_id` (`""`): they are the funnel's first and last lines.

## Building the funnel

Per step, in flow order:

- `reached` = `users` for `appcues:step_started` on that step
- `completed` = `users` for `appcues:step_completed`
- `skipped` = `users` for `appcues:step_skipped`
- `errors` = `events` for `appcues:step_error`
- `drop %` = `(reached − completed) / reached × 100`, one decimal;
  `—` when reached is 0

The flow line: `shown` = users for `appcues:flow_started`, `completed` =
users for `appcues:flow_completed`, completion rate =
`completed / shown × 100`, one decimal, `—` when shown is 0. The
biggest drop is the step with the largest `reached − completed`.

## Self-correcting on errors

The server is the only validator. A 400 names the offending field in
`detail` (on the CLI, `body.detail` in the one-line stderr JSON): fix
that field and retry once.

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
State empty sections; never omit them.

```
Appcues step drop-off — <flow name> (<flow_id>): <shown> shown, <completed> completed (<r.r%>), <period start date> → <period end date>

## Biggest drop
<one sentence naming the step, users lost, and its skip and error counts>

## Funnel
| # | step_id | reached | completed | skipped | errors | drop % |
|---|---|---|---|---|---|---|

## Steps with errors
- step <#> <step_id>: <n> errors

## Period & data notes
- Period: <start_time> → <end_time>.
- Data caveats: <"rows truncated" if the marker appeared, "no activity in period" when shown is 0, otherwise "none">.
```

- **Funnel**: every step in flow order; render `—` for undefined rates.
  Empty: "no step activity in period".
- **Steps with errors**: steps with errors > 0, sorted by errors
  descending. Empty: "no step errors".

## Rules

- Read-only: never create, publish, unpublish, or delete anything.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails after one self-correction, stop and report
  exactly what failed, quoting the structured error line.
- Default to a 7-day window; use another length only when the request
  names one.
