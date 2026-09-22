# Where selectors live in `get_experience_details`

Trimmed real payloads (ids shortened, content removed). The tool returns
one object per call; `state=published` selects the live snapshot, which
exists only for published content.

## Legacy flow (`flows list`, type `legacy flow (web)`)

Top-level key is `flow`. Steps are a map keyed by step id. Anchor
selectors live on `hotspot-group` and `tooltip-group` steps, one per
hotspot. `selectorSettings.selector` duplicates `selector`; read
`selector`.

```json
{
  "flow": {
    "id": "e02ec362-…", "name": "…", "type": "journey", "published": true,
    "steps": {
      "75030811-…": { "stepType": "modal", "index": 0 },
      "a1b2c3d4-…": {
        "stepType": "hotspot-group", "index": 1, "sequential": true,
        "hotspots": {
          "9f8e7d6c-…": {
            "index": 0,
            "selector": ".container--card [type=\"submit\"]",
            "selectorSettings": { "selector": ".container--card [type=\"submit\"]" },
            "includeTextMatchSelector": false,
            "includeOrderedMatchSelector": false
          }
        }
      }
    }
  },
  "rule": {
    "contentType": "journey", "frequency": "once", "published": true,
    "conditions": {
      "and": [
        { "or": [ { "url": { "operator": "*", "value": "/" } } ] },
        { "or": [ { "domains": { "operator": "==", "value": "app.example.com" } } ] }
      ]
    },
    "conditionsFlatMap": { "domains": ["app.example.com"] }
  }
}
```

Other legacy `stepType` values seen: `modal`, `action`. They carry no
anchor selector.

## Flows 2.0 (`experiences list flows-v2`, type `flow (web)`)

Top-level key is `experience`. Steps are an array; each step has an
array of `traits`. A `tooltip` step's anchor is the `@appcues/overlay`
trait whose `config.target.selector` is not internal. The same step
usually carries a second `@appcues/overlay` whose target is
`#tooltip-anchor` (internal: it points at the first overlay's `rootId`).

```json
{
  "experience": {
    "id": "…", "name": "Create Project Tooltip", "type": "flow", "platform": "web",
    "state": "PUBLISHED", "published": true,
    "steps": [
      {
        "id": "…", "type": "tooltip", "index": 0, "name": "Tooltip",
        "traits": [
          { "type": "@appcues/overlay",
            "config": { "rootId": "tooltip-anchor", "placement": "center",
                        "target": { "selector": "[aria-label=\"Add card\"]" } } },
          { "type": "@appcues/overlay",
            "config": { "rootId": "tooltip-root", "arrowId": "tooltip-arrow", "placement": "auto",
                        "target": { "selector": "#tooltip-anchor" } } },
          { "type": "@appcues/dialog", "config": { "target": "", "backdrop": "soft" } },
          { "type": "@appcues/scroll-into-view", "config": { "target": {} } },
          { "type": "@appcues/animate", "config": { "target": { "selector": "#flow-root" } } }
        ]
      },
      {
        "id": "…", "type": "flow", "index": 1,
        "traits": [
          { "type": "@appcues/floating", "config": { "target": { "selector": "flow-root" } } }
        ]
      }
    ]
  },
  "rule": { "conditions": { "and": [ … ] }, "conditionsFlatMap": { "domains": ["app.example.com"] } }
}
```

Only the first overlay is the anchor. A `flow` (modal) step's
`@appcues/floating` target is Appcues' own container; skip it. An
overlay whose anchor selector is `""` means the target was never set
in the builder: report it as `(empty)`.

## Pin (`experiences list pins`, type `pin`)

Same envelope as Flows 2.0. The anchor is the `@appcues/inline` trait's
`config.target.selector`; both the `button` step (the beacon) and the
`tooltip` step carry it, normally with the same value, so report it
once per pin. The tooltip step's `@appcues/overlay` targets
`#beacon-1`, the beacon's `targetId`: internal.

```json
{
  "experience": {
    "id": "40dbe68b-…", "name": "test pin", "type": "persistent", "platform": "web",
    "steps": [
      { "type": "button", "traits": [
          { "type": "@appcues/inline",
            "config": { "placement": "inner-right", "target": { "selector": "[href=\"/experiences/new\"]" } } } ] },
      { "type": "tooltip", "traits": [
          { "type": "@appcues/toggle",  "config": { "targetId": "tooltip-1" } },
          { "type": "@appcues/inline",  "config": { "target": { "selector": "[href=\"/experiences/new\"]" } } },
          { "type": "@appcues/overlay", "config": { "rootId": "tooltip-1", "arrowId": "customArrow",
                                                    "target": { "selector": "#beacon-1" } } } ] }
    ]
  },
  "rule": {
    "conditions": {
      "and": [
        { "and": [ { "url": { "operator": "regex", "value": ".*" } } ] },
        { "or":  [ { "domains": { "operator": "==", "value": "app.example.com" } } ] }
      ]
    },
    "conditionsFlatMap": { "domains": ["app.example.com"] }
  }
}
```

## Rule clauses

`rule.conditions` is a boolean tree of `and` / `or` arrays. The leaves
that matter here:

- `{"url": {"operator": <op>, "value": <pattern>}}`: page targeting.
  Operators seen: `*` (contains), `==` (exact), `$` (ends with),
  `^` (starts with), `regex`, and their negations. Report them as
  `<op> <value>`, e.g. `* /dashboards/`.
- `{"domains": {"operator": "==", "value": <host>}}`: domain
  targeting. `conditionsFlatMap.domains` is the same list flattened;
  use it for the domain filter. Empty means no domain restriction.

## Internal selectors to ignore

`flow-root`, `#flow-root`, and `#<rootId>` / `#<targetId>` of any trait
in the same step (`#tooltip-anchor`, `#tooltip-root`, `#beacon-1`,
`#tooltip-1`). They address Appcues' own DOM, never the customer's.

## Analytics and issues envelopes

`get_experience_analytics` (`dimension=all`) answers in prose:

```
Flow <id> analytics between 2026-09-16 and 2026-09-22:
- Seen: 19 unique users
- Completed: 0 users
- Skipped: 0 users
- Interacted: 0 users
- Errors: 19 users
```

Pins report `Dismissed` where flows report `Completed`/`Skipped`. Read
every line; the set varies. `list_experience_issues` returns recent
error samples with a message per sample, or the sentence
`No recent issues found.` `list_issue_spikes` returns flagged
experiences, or `No issue spikes detected.`
