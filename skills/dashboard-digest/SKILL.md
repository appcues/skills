---
name: dashboard-digest
description: Use when asked to explain, summarize, narrate, or report on an Appcues dashboard, what a dashboard or its charts show, what changed on a dashboard this week, or for a written digest of dashboard metrics. Walks an existing dashboard card by card with the numbers and the change vs the previous window.
---

# Appcues dashboard digest

Turn an existing dashboard into a written report: one entry per card,
saying what the card measures, the current value, and the change against
the previous window of the same length. Read-only: this skill only reads
dashboards and runs their saved queries, it never creates, edits, or
deletes a dashboard or a card.

## Getting the data

Dashboards live only on the account tools (the MCP tool set); the public
API has no dashboard routes. Use whichever of these you have:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH, calling the tools:

   ```bash
   appcues status                                                        # verify credentials
   appcues tools call list_dashboards -o json                            # id, name per dashboard
   appcues tools call get_dashboard --attr dashboard_id=<ID> -o json     # attached items: query views, funnels, widgets
   appcues tools call execute_query_view --attr query_view_id=<QV_ID> --attr dashboard_id=<ID> --attr trailing_days=7 -o json
   appcues tools call render_funnel --attr funnel_id=<F_ID> --attr trailing_days=7 -o json
   ```

   Run `execute_query_view` and `render_funnel` twice per card: once
   with `trailing_days=7` for the current window, once with explicit
   `start_time`/`end_time` for the 7 days before it. Percentage metrics
   come back as ratios (0.167 means 16.7%).

   If the first `tools call` fails with exit 5 and a body saying MCP
   server access is not available for this account, or exit 3 because
   the environment has no tools service, stop and report that: there is
   no other source for dashboards.

2. **The Appcues MCP server's tools** `list_dashboards`,
   `get_dashboard`, `execute_query_view`, `render_funnel`, when there is
   no shell or no binary. `explain_query_view` returns a card's
   definition together with its rendered result and is the better call
   when the card's meaning is unclear; it requires `start_time`,
   `end_time`, `time_dimension`, and, on a campaign or tactic
   dashboard, `template`.

Use one access path for the whole task. Never reconstruct a request with
curl or raw HTTP because an output looks wrong or a call failed; read
the structured error and act on it. Local parsing of results (python3,
jq) is fine.

Credentials are ambient (the environment, or the CLI's own config, which
the CLI reads itself). Never read, print, or search for credential files
or secret values; on an auth failure, stop and report what is missing.

### Which dashboard

Use the dashboard the request names (by name or id). If it names none,
list dashboards and report every one, in listing order, up to three; say
in the notes how many were skipped. If the account has none, emit the
skeleton once with the heading "Appcues dashboard digest — no dashboards
in this account" and every section set to "no dashboards", then stop.
Never ask which.

### Card types

`get_dashboard` returns the attached items. Handle each by kind:

- **Query view**: run it for both windows; the card's headline metric
  is the first metric it returns, and its label is the card's name.
- **Funnel**: render it for both windows; report users at the first
  and last step and the overall conversion (`conversion_from_start` of
  the last step).
- **Widget**: static content (text, notes). Report its title and skip
  the numbers line.

A card whose query returns an error or no rows is reported as "no data
in window", never dropped.

## Self-correcting on errors

The server is the only validator. A tool argument error names the
missing or invalid field; fix it and retry once. The CLI fails loud and
structured: non-zero exit, one JSON line on stderr.

| exit | meaning | do |
|---|---|---|
| 0 | success | continue |
| 1 | unexpected failure | stop, report the JSON `message` |
| 2 | usage error | fix the invocation, retry once |
| 3 | missing/bad credentials, or no tools service | stop, report exactly what is needed |
| 4 | tool rejected the arguments, or ran and reported failure | fix the field named, retry once; on `type: "tool"` report the envelope |
| 5 | rate limited / 5xx (already retried) | stop, report |

## Report format (MUST)

Emit exactly this structure per dashboard: same sections, same order,
same headings. State empty sections; never omit them.

```
Appcues dashboard digest — <dashboard name> (<dashboard_id>): <n> cards, <period start date> → <period end date> (vs the previous 7 days)

## Headline
<one or two sentences: the card that moved most and the direction, or "no card moved more than 5%">

## Cards
| card | type | now | previous | Δ |
|---|---|---|---|---|

## Card notes
- <card name>: <one sentence saying what it measures in plain business terms and what the change means; no causes the chart does not establish>

## Period & data notes
- Current window: <start_time> → <end_time>; previous: <start_time> → <end_time>.
- Cards without data: <names, or "none">.
- Dashboards not covered: <"none" or the names skipped beyond the first three>.
```

- **Cards**: every attached item, in the dashboard's order. Percentages
  shown as percentages (16.7%, not 0.167). Δ as a percent change for
  counts and as points for rates; `new` when the previous value is 0;
  `—` for widgets.
- **Card notes**: one bullet per query view and funnel, none for
  widgets. Use unique users, conversion rate, accounts, sessions, and
  events per user as vocabulary.

## Rules

- Read-only: never create, update, arrange, or delete dashboards or
  cards.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails after one self-correction, stop and report
  exactly what failed, quoting the structured error line.
- Always a 7-day window unless the request names another length; the
  previous window is derived, never asked for.
