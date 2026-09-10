---
name: nps-sentiment
description: Use when asked how an Appcues NPS survey is doing, what customers are saying in NPS feedback, for NPS themes or sentiment, why the NPS score moved, or for a detractor/promoter comment summary. Combines the computed NPS score trend with a reading of the raw written replies.
---

# Appcues NPS score and sentiment

Report an NPS survey's score today against the score 30 days ago, then
read every written reply from the last 30 days, group them into themes,
and say whether what people write agrees with the number. Read-only: this skill only queries
and exports analytics, it never creates, publishes, or deletes anything.

## Getting the data

Three datasets are needed, all scoped to one NPS survey by its id:

- **Surveys**: which NPS surveys the account has (classic and 2.0).
- **Score series**: the NPS score with promoter, neutral, and detractor
  counts per day over the last 30 days. Every value is a rolling 30-day
  figure as of that day, so the last day is "the score now" and the
  first day is "the score 30 days ago" (covering the previous 30-day
  window). Respondents = promoters + neutrals + detractors on the same
  day.
- **Replies**: one row per respondent with `timestamp`, `score`,
  `category`, `feedback` for the last 30 days.

The account tools (the MCP tool set, also callable from the CLI) return
all three directly and handle classic and 2.0 surveys alike; the
analytics spec route is the fallback for accounts without tool access.
Use whichever Appcues access you have, in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. First the tools:

   ```bash
   appcues status                                                          # verify credentials
   appcues tools call list_experiences --attr type=nps -o json              # surveys: id,name,type,status CSV
   appcues tools call get_nps_metrics --attr nps_id=<ID> --attr dimension=day --attr format=csv -o json
   appcues tools call list_nps_responses --attr nps_id=<ID> --attr last_days=30 --attr limit=1000 -o json
   ```

   `get_nps_metrics` defaults to the last 30 days and prints
   `day,nps_score,promoters,neutrals,detractors,respondents`, **omitting
   days with no respondents**, so the series is usually sparse and its
   first row is not "30 days ago". `list_nps_responses` prints
   `timestamp,user_id,score,category,feedback` with score and feedback
   already paired per respondent.

   If the first `tools call` fails with exit 5 and a body saying MCP
   server access is not available for this account, or exit 3 because
   the environment has no tools service, switch to the analytics specs
   for the rest of the task (this is the one sanctioned tier change, it
   is decided once, up front). Copy the reference specs, replace
   `<NPS_FLOW_ID>` (see "Which survey" below) and the placeholder dates,
   then:

   ```bash
   appcues analytics query --spec nps-surveys.json -o json           # discover survey ids with data
   appcues analytics query --spec nps-score.json -o json             # one row per day
   appcues analytics query --spec nps-feedback.json --async -o json  # prints {job_id, status}
   appcues jobs download <JOB_ID> --out nps-feedback-rows.json       # waits, then writes the rows
   ```

   All specs take the same explicit 30-day `start_time`/`end_time`
   ending now. Keep 30 days: the computed score is a 30-day rolling
   figure, so a shorter window only truncates the series.

2. **The Appcues MCP server's tools** `list_experiences` (with
   `type: "nps"`), `get_nps_metrics` (`nps_id`, `dimension: "day"`),
   and `list_nps_responses` (`nps_id`, `last_days: 30`), when there is
   no shell or no binary. Same outputs as above.

3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort, with the reference specs: `POST .../analytics/query` for
   survey discovery and the score series, `POST .../analytics/exports`
   then `GET .../analytics/exports/{job_id}` for the replies; the
   `download_url` on a `done` job is fetched with no auth headers. The
   public `/nps` route lists NPS 2.0 surveys only, never classic ones.

Pick the first tier available and use it exclusively for the whole task:
this is an availability ladder, not a troubleshooting ladder. When the
CLI is present, every Appcues API interaction goes through it; never
reconstruct a request with curl or raw HTTP because an output looks wrong
or a call failed. Local parsing of results (python3, jq) is fine.

Credentials are ambient (the environment, or the CLI's own config, which
the CLI reads itself). Never read, print, or search for credential files
or secret values; on an auth failure, stop and report what is missing.

### Which survey

Use the NPS survey the request names (a Studio NPS URL contains its id:
`studio.appcues.com/nps/<id>/edit`). If it names none, take every
survey `list_experiences type=nps` returns (its `name` column is the
survey name), published ones first; on the analytics fallback, run
`references/nps-surveys.json` and take every distinct `flow_id`, ordered
by `users` descending, with the id as the name. Never ask which. The
public API's `experiences list nps` command shows NPS 2.0 surveys only,
so an empty result there is not "no NPS". If there are no surveys at
all, emit the report skeleton once with the heading line "Appcues NPS —
no NPS surveys in this account" and every section set to "no NPS
surveys", then stop.

### Field names that work

Use exactly the fields in the reference specs; these shapes were
verified against the API. Known server failures (500, not a spec error,
do not retry): the `nps_respondents` metric anywhere in a spec;
`nps_computed_score` with any dimension other than `day` (or with
`nps_scores_submitted` alongside); the raw columns
`nps_raw_score`/`nps_feedback` (`score` and `feedback` are the working
names).

## Reading the score series

"Now" is the row for the latest day in the series. "30 days ago" is the
row dated 30 days before that day; on the tool path that row is usually
absent, which means zero respondents and no score then: show `—` for
the NPS and `0` for the counts, and report the Δ as "new" rather than a
number. Never reuse the "now" row as the baseline. The heading's period
is always the full 30-day window requested, not the span of rows
returned.

## Reading the replies

Work only from the rows you fetched. `list_nps_responses` rows are
already one per respondent with score and feedback paired. On the
analytics fallback the export is raw events: an
`appcues:nps_score_and_feedback` row carries its own `score`, while
classic NPS records the score and the written reply as separate events
(`appcues:nps_score`, then `appcues:nps_feedback`), so pair each
`appcues:nps_feedback` row with the same user's latest
`appcues:nps_score` row whose `timestamp` is at or before the
feedback's `timestamp`; never a later one. In both paths `user_id`
serves only that pairing and never appears in the report. Then, for
each reply with non-empty `feedback`:

1. Bucket by `score` (or the tool's `category`): 9–10 promoter, 7–8
   neutral, 0–6 detractor. A reply with no score is "unscored".
2. Assign one theme per reply from the text (for example pricing,
   onboarding, bugs, missing feature, support, performance, praise).
   Invent theme names from the replies; do not force a fixed list.
3. Count replies per theme, split by bucket.

Then compare: does the theme mix explain the score and its move? A
score that fell while detractor comments concentrate on one theme is a
finding; a score that fell with scattered themes is noise.

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

Emit exactly this structure per NPS flow: same sections, same order,
same headings. State empty sections; never omit them.

```
Appcues NPS — <flow name> (<flow_id>): score <s> (<±d> vs 30 days ago), <n> respondents, <period start date> → <period end date>

## Score
| | now (<last day>) | 30 days ago (<first day>) | Δ |
|---|---|---|---|
| NPS | | | |
| respondents | | | |
| promoters | | | |
| neutrals | | | |
| detractors | | | |

## Trend
<one sentence: lowest and highest daily score in the series with their dates, or "flat">

## What people wrote
<one or two sentences: how many replies had text, and whether the themes agree with the score move>

## Themes
| theme | replies | promoters | neutrals | detractors | unscored |
|---|---|---|---|---|---|

## Detractor voices
- "<verbatim reply, ≤200 chars>" (score <n>)

## Promoter voices
- "<verbatim reply, ≤200 chars>" (score <n>)

## Period & data notes
- Period: <start_time> → <end_time>; series of <n> days.
- Replies with text: <n> of <total respondents>.
- Data caveats: <"rows truncated" if the marker appeared, "no respondents 30 days ago" when the first day's respondents is 0, otherwise "none">.
```

- **Themes**: sorted by replies descending. Empty: "no written replies".
- **Detractor voices / Promoter voices**: at most 5 each, most recent
  first, verbatim, no paraphrase. Empty: "none".
- Never output `user_id` values, or emails, anywhere in the report,
  including the data notes; replies are quoted anonymously.
- The report is the whole answer: nothing before the heading line,
  nothing after the last data note. Interpretation belongs in "What
  people wrote"; caveats belong in the data-caveats line.

## Rules

- Read-only: queries and exports only.
- Run unattended: never ask the user questions. If credentials are
  missing or a call fails after one self-correction, stop and report
  exactly what failed, quoting the structured error line.
- Always a 30-day window ending now; "30 days ago" is the first day of
  the series, never a separate query.
