---
name: campaign-report
description: Use when asked how an Appcues campaign is doing, for a campaign report or status, what tactics or content a campaign has, whether the campaign objective is being met, or which campaign content is still in draft. Reports one campaign end to end with engagement vs the previous period.
---

# Appcues campaign report

Report one campaign end to end: its objective, each tactic, the content
placed in each tactic with its published state, and each content
item's engagement over the last 30 days against the 30 days before.
Read-only: this skill only reads campaigns and analytics, it never
creates, publishes, or deletes anything.

## Getting the data

Campaigns and tactics live only on the account tools (the MCP tool
set); the public API has no campaign routes. Use whichever of these you
have:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH, calling the tools:

   ```bash
   appcues status                                                        # verify credentials
   appcues tools call list_campaigns -o json                             # id, name, description per campaign
   appcues tools call get_campaign --attr campaign_id=<ID> -o json       # brief, objective, tactics (id, name, contents_count)
   appcues tools call get_tactic --attr tactic_id=<T_ID> -o json         # content: id, name, type, status, brief
   appcues tools call get_experience_analytics --attr experience_id=<C_ID> --attr dimension=all --attr start_date=<YYYY-MM-DD> --attr end_date=<YYYY-MM-DD> -o json
   appcues tools call get_objective --attr objective_id=<O_ID> -o json   # only when get_campaign shows an objective
   ```

   Run `get_experience_analytics` twice per content item: the last 30
   days, then the 30 days before. It prints seen, completed, skipped,
   interacted, and errors as unique users, and omits content with no
   events in the range: treat that as zeros. Checklist items need
   `get_checklist_item_analytics` instead; NPS content needs
   `get_nps_metrics`.

   If the first `tools call` fails with exit 5 and a body saying MCP
   server access is not available for this account, or exit 3 because
   the environment has no tools service, stop and report that: there is
   no other source for campaigns.

2. **The Appcues MCP server's tools** `list_campaigns`, `get_campaign`,
   `get_tactic`, `get_experience_analytics`, `get_objective`, when
   there is no shell or no binary. Same outputs as above.

Use one access path for the whole task. Never reconstruct a request with
curl or raw HTTP because an output looks wrong or a call failed; read
the structured error and act on it. Local parsing of results (python3,
jq) is fine.

Credentials are ambient (the environment, or the CLI's own config, which
the CLI reads itself). Never read, print, or search for credential files
or secret values; on an auth failure, stop and report what is missing.

### Which campaign

Use the campaign the request names (by name or id; `list_campaigns`
accepts a name search). If it names none and the account has exactly
one, use it; with several, report each in listing order, up to three,
and say in the notes how many were skipped. If there are none, emit the
skeleton once with the heading "Appcues campaign report — no campaigns
in this account" and every section set to "no campaigns", then stop.
Never ask which.

### Objective

`get_campaign` returns `objective: null` or an objective id. With an
id, `get_objective` reports the objective's name, whether it is
complete, which fields it still lacks, and its key moment. Report that
verbatim; do not compute progress unless the objective names a key
moment and a direction, in which case the key moment's event count for
both windows is the progress line.

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

Emit exactly this structure per campaign: same sections, same order,
same headings. State empty sections; never omit them.

```
Appcues campaign report — <campaign name> (<campaign_id>): <t> tactics, <c> content items (<p> published), <period start date> → <period end date> (vs the previous 30 days)

## Objective
<the objective's name and completeness as returned, and its progress line when computable; or "no objective set">

## Summary
<one or two sentences: total unique users who saw campaign content in the window, the change vs the previous window, and which tactic carried most of it>

## Tactics
### <tactic name> (<tactic_id>)
| content | type | status | seen | completed | completion % | Δ seen |
|---|---|---|---|---|---|---|

## Not live
- <content name> (<tactic name>): <status>

## Period & data notes
- Current window: <start_time> → <end_time>; previous: <start_time> → <end_time>.
- Content with no events in either window: <names, or "none">.
- Campaigns not covered: <"none" or the names skipped beyond the first three>.
```

- **Tactics**: one subsection per tactic in the campaign's order; every
  content item in the tactic's order. `completion %` is completed /
  seen as a percent, `—` when seen is 0. `Δ seen` is the percent change
  in unique users seen, `new` when the previous value is 0. A tactic
  with no content: "no content".
- **Not live**: every content item whose status is not PUBLISHED,
  sorted by tactic then name. Empty: "all content is published".
- Never output user identifiers or emails.

## Rules

- Read-only: never create, update, publish, or delete campaigns,
  tactics, or content.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails after one self-correction, stop and report
  exactly what failed, quoting the structured error line.
- Always a 30-day window unless the request names another length; the
  previous window is derived, never asked for.
