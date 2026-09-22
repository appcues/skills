---
name: selector-check
description: Use when asked whether published Appcues tooltips or pins still target valid elements, to audit CSS selectors before a deploy, release, or merge, whether a frontend change broke Appcues content on a domain, which flows or pins have selector misses or "target not found" errors, or to get suggested stable selectors from the app's source. Cross-checks every published selector against live miss rates and, when run inside the web app's repository, against its source code.
---

# Appcues selector check

Audit every published web experience that anchors to a CSS selector
(tooltip steps in legacy flows and Flows 2.0, and pins): what each
selector is, how often it misses in production, whether the current
source tree still produces an element that matches it, and what a more
stable selector would be. Read-only: this skill only queries the
account and reads the repository. It never publishes, edits an
experience, or changes a file. Retargeting is done by a human in the
builder; the report tells them what to enter.

The source check is static. It proves a selector is absent or brittle;
it never proves the tooltip will render. Say so in every report.

## Inputs

All optional, taken from the request; never ask for them.

- **Domain**: the host the app deploys to.
  With a domain, only experiences whose domain targeting includes it
  are audited. Without one, every published selector-bearing
  experience is audited and the notes say so.
- **Window**: days of analytics, default 7, 1–90.
- **Source tree**: the current working directory when it contains a
  web app (a `package.json`, `src/`, or templates). Without one, the
  source verdict for every selector is `no source available` and the
  report is a live scoreboard only.

## Getting the data

Use whichever Appcues access you have, in this order:

1. **The `appcues` CLI**, when you have a shell and the binary is on
   PATH. Always pass `-o json`. Anything without a typed command is
   reachable as `appcues tools call <name>`; tool names are identical
   on the CLI and the MCP server, so name a tool once for both.
2. **The Appcues MCP server's equivalent tools**, when there is no shell
   or no binary.
3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
   resort.

Pick the first tier available and use it exclusively for the whole
task: this is an availability ladder, not a troubleshooting ladder. A
failed call is never a reason to drop a tier; read the structured
error and act on it. Local parsing (python3, jq,
grep) is fine.

Credentials are ambient (the environment, or the CLI's own config,
which the CLI reads itself). Never read, print, or search for
credential files or secret values; on an auth failure, stop and report
what is missing.

### Step 1: candidates

List published web content of the three selector-bearing kinds.

```bash
appcues status -o json                                  # verify credentials, note the account id
appcues flows list -o json                              # legacy flows: keep "published": true
appcues experiences list flows-v2 -o json               # Flows 2.0: keep "published": true
appcues experiences list pins -o json                   # pins: keep "published": true
```

On the MCP tier use `list_experiences` and keep rows whose status is
`PUBLISHED` and whose type is `legacy flow (web)`, `flow (web)`, or
`pin`. Sort candidates by `published_at` descending and stop after 50;
if more exist, say how many were skipped in the notes.

### Step 2: selectors and targeting, one call per candidate

```bash
appcues tools call get_experience_details --attr id=<ID> --attr state=published -o json
```

One payload carries both the live content and its rule. Where the
selectors and the rule live differs per kind; the exact paths, with
trimmed real samples, are in `references/payload-shapes.md` (relative
to this skill's directory). In short:

| kind | anchor selector path | page rule |
|---|---|---|
| legacy flow | `flow.steps.<step>.hotspots.<hotspot>.selector` on steps whose `stepType` is `hotspot-group` or `tooltip-group` | `rule.conditions` (`url` and `domains` clauses) |
| Flows 2.0 | `experience.steps[].traits[]` where `type` is `@appcues/overlay`: `config.target.selector`, on steps whose `type` is `tooltip` | `rule.conditions` |
| pin | `experience.steps[].traits[]` where `type` is `@appcues/inline`: `config.target.selector`; identical values across a pin's steps count once | `rule.conditions` |

Ignore **internal selectors**: Appcues' own DOM, never the customer's.
A selector is internal when it is `flow-root`, `#flow-root`, or `#`
followed by the `rootId` or `targetId` of another trait in the same
step (observed: `#tooltip-anchor`, `#beacon-1`). Also ignore selectors
on `@appcues/floating`, `@appcues/animate`, `@appcues/dialog`, and
`@appcues/scroll-into-view` traits; they position Appcues' own
container. An empty anchor selector (`""`) is a finding, not an
exclusion: report it as `current: (empty)`.

Domain filter: `rule.conditionsFlatMap.domains` lists the targeted
hosts. With a domain in the request, keep the experience when the list
contains it (exact host, or a wildcard pattern that matches it) or
when the list is empty. Record the `url` clauses (operator + value) as
the page rule; they matter for the suggestions.

Drop candidates with no anchor selectors after this step; they are
modals, slideouts, or empty pins, not selector content.

### Step 3: live miss rate, two calls per kept experience

```bash
appcues tools call get_experience_analytics --attr experience_id=<ID> --attr last_days=<N> --attr dimension=all -o json
appcues tools call list_experience_issues --attr experience_id=<ID> -o json
appcues tools call list_issue_spikes -o json             # once, for the whole account
```

The analytics tool answers in prose: one line per operation with a
unique-user count (`Seen`, `Completed`, `Skipped`, `Dismissed`,
`Interacted`, `Errors`; the set varies by kind). Record every line.
Miss rate is **unique users with errors ÷ unique users seen**. Seen
counts SDK start attempts, so Seen = Errors with zero completions or
dismissals means the content never rendered; and the same user can be
in both counts, so 20 error users of 23 seen does not mean 3 clean
renders. Both caveats appear verbatim in the report.

`list_experience_issues` returns recent error samples with messages;
keep the most recent message per experience, or `no recent message`
when it says no issues were found. `list_issue_spikes` names
experiences whose error rate jumped; mark them in the scoreboard. If
either tool fails with exit 5 and a body saying account tools are not
available, or exit 3 because there is no tools service, fill those
columns with `account tools unavailable` and continue.

### Step 4: source verdict, when a source tree is present

For each selector, split it into its discriminating parts: tag names,
`#id`, `.class` tokens, `[attr="value"]` pairs, `nth-*` and
`data-sentry-*` fragments. Search the tree for the parts that identify
an element (ids, attribute values, distinctive class tokens, aria
labels, hrefs, `data-testid` values), skipping build output,
`node_modules`, lockfiles, and vendored assets. Then assign one verdict:

| verdict | meaning |
|---|---|
| `found` | every identifying part appears in source on an element that plausibly renders on the page rule's URL, with combinators (`#a .b`) traced to real nesting, and the selector uses no brittle construct |
| `found but brittle` | the parts appear, but the selector depends on a construct in the "Do not use" list |
| `not found` | an identifying part appears nowhere in source, or the parts exist but their nesting cannot be traced |
| `no source available` | no source tree, or the tree is not a web app |

The brittle constructs, fixed:

- **Exact class equality** `[class="a b c"]`: utility class order and
  extra classes break equality on every rebuild.
- **Positional chains** `nth-child`, `nth-of-type`, long descendant
  paths: any sibling added or removed breaks them.
- **Build-artifact attributes** `data-sentry-*`, `data-reactid`,
  hashed CSS-module class names: annotations, not a contract.
- **Bare tag names** `aside`, `h1`, `button`: match several elements
  or the wrong one; also flag when the source has more than one on
  the page.
- **Empty selector**: nothing to match.

Name the source file and component behind each verdict so the reader
can jump to it.

### Step 5: suggestions

For every selector that is not `found`, propose one replacement built
from attributes the source already has, in this order of preference:
`data-testid` or `data-appcues` style hooks, `id`, `aria-label`,
`href`, a stable semantic tag plus attribute (`nav[aria-label="…"]`),
then a stable class name that is written literally in source. Mark it:

- **Now**: the attribute exists; retarget in Appcues with no app change.
- **Needs attr**: one attribute must be added to a named element
  first; give the exact attribute and value.

When the page rule contributes to the misses (a `url` clause that also
matches pages where the element never renders, or excludes the page it
lives on), say so in the same block and give the tightened rule. With
no source, suggest nothing beyond "avoid" for brittle constructs; do
not invent attributes.

## Self-correcting on errors

| exit | meaning | do |
|---|---|---|
| 0 | success | continue |
| 1 | unexpected failure | stop, report the JSON `message` |
| 2 | usage error | fix the invocation, retry once |
| 3 | missing/bad credentials | stop, report exactly what is needed |
| 4 | API rejected the request (4xx) | stop, report status and message; a 404 on one experience drops it with a note |
| 5 | rate limited / 5xx (already retried) | stop, report |

## Report format (MUST)

Emit exactly this structure: same sections, same order, same headings.
State empty sections; never omit them.

```
Appcues selector check — <n> selector-bearing experiences on <domain or "all domains">, <b> broken, <r> brittle, <window start> → <window end>, source <"checked <ref or date>" | "not available">

## Seen is not a successful render
Seen counts SDK start attempts, Errors counts selector misses, and one user can be in both. Seen = Errors with zero completions or dismissals means the content never rendered. Miss rate is unique users with errors ÷ unique users seen; overlap is allowed, so the difference is not a count of clean renders.

## Summary
| Verdict | Count |
|---|---:|
| Totally broke (100% miss, 0 complete/dismiss) | <n> |
| Nearly broke (≥ 80% miss) | <n> |
| Flaky (20–79% miss) | <n> |
| Working (< 20% miss) | <n> |
| No traffic in window | <n> |

## Scoreboard
| Experience | Kind · ID | Seen | Errors | Miss | Complete / dismiss | Source | Spike | Verdict |
|---|---|---:|---:|---:|---:|---|---|---|

## Per selector
### <experience name>
- **Kind:** <legacy flow | flow 2.0 | pin> · **Step:** <step name or index>
- **Current:** `<selector>` or (empty)
- **Page rule:** <url clauses, e.g. `* /dashboards/`>
- **Source:** <verdict> — <file/component, one sentence why>
- **Live:** <errors>/<seen> unique users (<miss%>); latest message: "<message>" or no recent message
- **Suggested:** `<selector>` — <Now | Needs attr on <component>: <attr="value">> | no suggestion without source

## Retarget in Appcues now
1. <experience> → `<selector>`<, tighten page rule to …>

## Add one source attribute, then retarget
1. <component/file>: `<attr="value">` — unblocks <experience list>

## Do not use
- <brittle construct seen in this account, one line each, or "none seen">

## Window & data notes
- Window: <start> → <end> (<N> days); account <id>; domain filter <"host" | "none">.
- Candidates: <n> published, <k> kept after selector/domain filter, <s> skipped by the 50 cap.
- Source: <"tree at <path>, checked <git ref or date>" | "none">. Static check only; a `found` verdict does not prove a render.
- Tools: <"ok" | "account tools unavailable: issues and spikes not checked">.
```

- **Summary** buckets use miss rate; "No traffic" is Seen = 0. An
  experience is "Totally broke" only when Seen > 0, Errors = Seen, and
  every completion/dismissal count is 0.
- **Scoreboard**: sorted by miss rate descending, then Errors
  descending; no-traffic rows last, sorted by name. `Miss` is `—` when
  Seen = 0. `Spike` is `yes`, `no`, or `n/a`.
- **Per selector**: one block per anchor selector, in scoreboard
  order; an experience with several tooltip steps gets several blocks
  under one heading. Truncate messages longer than 120 characters
  with `…`.
- **Retarget now** lists every `Now` suggestion; **Add one source
  attribute** lists every `Needs attr`, grouped by element so one
  attribute that unblocks two experiences appears once. Empty: "none".
- **Do not use**: the brittle constructs actually observed, each with
  one reason. Empty: "none seen".

## Rules

- Read-only: never publish, unpublish, update a rule or step, or
  modify a file in the repository. Suggestions are text for a human.
- Run unattended: never ask the user questions. Missing domain means
  all domains; missing source means a live-only report; a failed
  call after one self-correction stops the run with the structured
  error quoted.
- Never claim a selector works. The strongest positive verdict is
  `found`, and the header line says the check is static.
