# The query spec, field by field

A spec is one JSON object. Its shape picks the result: `metrics` +
`dimensions` returns computed aggregates (one row per dimension
combination); `columns` returns raw event rows. Everything here was
verified against the live API; the server remains the only validator,
and an invalid field comes back as a structured 400 naming it.

| Field | Type | Meaning |
|---|---|---|
| `metrics` | array of strings | What to compute per row. General metrics: `users`, `events`, `sessions`, `groups`. Specialized metrics exist (e.g. `nps_computed_score`, `nps_promoters`, which require a `flow_id` condition); see "Metrics the engine accepts" below for the verified list and limits. |
| `dimensions` | array of strings | What to group by. Time buckets: `day`, `week`, `month` (missing buckets are zero-filled). Grouping fields: `name` (event name, alias `event`), `flow_id`, and others. |
| `columns` | array of strings | Raw mode: which event fields to return, one row per event. Known-good: `timestamp`, `user_id`, `name` (alias `event`). |
| `conditions` | array of triples | Filters, AND-ed together. Each is `[field, operator, value]`. Operators: `==`, `!=`, `in`, `not in` (list value), plus pattern forms (`like`, `ilike`, `not like`, `not ilike`). Example: `["name", "in", ["appcues:flow_started", "appcues:flow_completed"]]`. |
| `order_by` | array of pairs | Sort: `[["events", "desc"], ...]`, where each pair is a selected field plus `"asc"` or `"desc"`. |
| `start_time`, `end_time` | string | The window, always set explicitly. `"YYYY-MM-DD"` or RFC 3339. Sync queries cap at 90 days. |
| `timezone` | string | IANA name (`"UTC"`, `"America/New_York"`); buckets and timestamps are adjusted to it. |
| `limit`, `offset` | integer | Row cap and paging. Sync results clamp at 1000 rows regardless. A `limit` in an async spec caps the export the same way, so omit it when you want the complete set. |
| `rank_n` | object | Top/bottom-N filter: `{"n": 5, "direction": "top", "dimension": "name"}`. Ranks the dimension's values by their metric total over the whole window, then returns the full timeseries for just those values. Include the ranked dimension in `dimensions`, and use the real column name (`name`, not its `event` alias). |

Rules that hold for every spec:

- Never include `account_id`; it comes from the authenticated context
  and any body value is ignored.
- `name` and `event` are interchangeable in `dimensions` and
  `conditions`; `rank_n.dimension` accepts only `name`.
- The server's 400 `detail` names anything invalid; the lists below
  come from the analytics engine's vocabulary and are the names to try
  first, not a guarantee that every one returns data for every account.

## Dimensions the engine accepts

Grouped by what they describe. Use them in `dimensions` and in
`conditions`; most also work as raw `columns`.

| Group | Names |
|---|---|
| Time | `day`, `week`, `month`, `timestamp` |
| Event | `name` (alias `event`), `event_type`, `source`, `platform`, `app_id`, `attributes`, `context` |
| Identity | `user_id`, `group_id`, `session_id`, `email`, `identity` |
| Flows | `flow_id`, `flow_version`, `flow_type`, `step_id`, `step_type`, `step_child_id`, `interaction_type`, `interaction_data` |
| Flow errors | `step_error_message`, `step_error_url` (with `appcues:step_error` and `appcues:v2:step_error`); `step_child_error_message`, `step_child_error_url` (with `appcues:step_child_error`) |
| Experiences | `experience_id`, `experience_type`, `survey_id`, `response_value`, `search_query` |
| Checklists | `checklist_id`, `checklist_item_id`, `item_id` |
| Goals & experiments | `goal_id`, `goal_version`, `experiment_id`, `experiment_group` |
| NPS | `score`, `feedback`, `window` (the engine also lists `nps_raw_score`/`nps_feedback`, but as raw `columns` they fail with a 500; use `score`/`feedback`) |
| Page | `url`, `hostname`, `path`, `hash`, `query`, `screen_id`, `context_url`, `current_page_url`, `last_page_url` |
| Device | `user_agent_browser`, `user_agent_os`, `user_agent_device`, `user_agent_cpu`, `user_agent_engine`, `locale_id`, `locale_name` |
| Membership | `segment_id`, `user_segment_id`, `campaign_id`, `tactic_id`, `user_group_id` |
| Profiles | `attribute_name`, `attribute_value`, `last_seen`, `last_updated` |

## Metrics the engine accepts

General: `users`, `events`, `sessions`, `groups`. NPS (require a
`flow_id` condition): `nps_computed_score`, `nps_promoters`,
`nps_detractors`, `nps_neutrals`, `nps_survey_started`,
`nps_scores_submitted`, `nps_feedbacks_submitted`. Every NPS value is a
rolling 30-day figure as of the bucket's day. Verified server limits:
`nps_computed_score` works only with the `day` dimension and not
alongside `nps_scores_submitted`; `nps_respondents` fails with a 500 in
any spec (sum promoters + neutrals + detractors instead). Others exist
(conversion, `avg_`/`median_`/`p90_`/`p99_` prefixes); the server's 400
names an unknown one.
