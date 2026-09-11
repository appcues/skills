# The skill contract

Every skill in this directory is authored against this contract. A skill
that meets it runs unchanged on every runtime that implements the
[Agent Skills](https://agentskills.io) standard (Claude Code, OpenClaw,
Hermes, ChatGPT/Codex, and whatever comes next). Background research:
`docs/cross-runtime-skill-portability.md` (the spec side) and
`docs/skill-ecosystem-survey.md` (what popular skill repos actually ship,
confirming this contract empirically).

## The skills

| Skill | What it answers |
|---|---|
| `account-inventory/` | What's in the account: flows, segments, tags, with counts |
| `analytics-query/` | Analytics questions: usage over time, top events, filtered metrics, raw event exports |
| `weekly-performance-digest/` | Weekly digest of published flows' performance: totals, top movers, completion regressions, vs the previous period |
| `experience-errors/` | Error-rate spikes per experience plus step errors by flow, step, and error message vs the previous period; new, rising, and resolved errors. Built for a daily run by an external scheduler |
| `nps-sentiment/` | One NPS survey's score trend plus themes and verbatim quotes from the written replies |
| `flow-step-dropoff/` | Step-by-step funnel of one flow: where users are lost, with skip and error counts |
| `dashboard-digest/` | Narrates an existing Appcues dashboard card by card: what each chart shows, the numbers, and the change vs the previous window |
| `campaign-report/` | One campaign end to end: objective, each tactic, its content with published state and engagement vs the previous period |
| `appcues-cli/` | How to drive the `appcues` CLI for ad hoc tasks: status and profiles, listings, publish/unpublish, tool discovery and calls, analytics exports. The fallback when no report skill matches |

## Format: spec-pure

- A skill is a directory with `SKILL.md` (YAML frontmatter + markdown
  body), plus optional `references/`, `scripts/`, `assets/`.
- Frontmatter uses only fields from the spec: `name`, `description`, and
  when genuinely needed `license`, `compatibility`, `metadata`. Anything
  else hard-fails claude.ai/Skills-API validation. Runtime-specific
  settings go under `metadata.<runtime>` (e.g. `metadata.openclaw`), which
  every other runtime ignores.
- `description` states when to use the skill (triggers, symptoms), never
  how it works. Front-load the triggers into the **first sentence**: some
  runtimes truncate the description to one line when routing, and a
  trigger that only appears in sentence two never fires there.
- No runtime-specific body features: no `$ARGUMENTS`, no backtick-command
  injection, no `${CLAUDE_*}` variables, no `@file` references. Outside
  their home runtime they arrive as literal text. Refer to bundled files
  by path relative to the skill directory, in plain prose.
- Self-contained: never reference another skill's files, this README, or
  anything in `runtimes/`. Skills install one at a time; everything the
  skill needs at run time must be inside its own directory. The test:
  delete `runtimes/` and the skill still describes complete work.

## Capabilities, not transports

State what the skill needs (listings, an export, a publish), then let the
agent use whatever Appcues access it has. Copy this access block into the
skill:

> Use whichever Appcues access you have, in this order:
>
> 1. **The `appcues` CLI**, when you have a shell and the binary is on
>    PATH. Always pass `-o json`. Anything without a typed command is
>    reachable as `appcues tools call <name>`; tool names are identical
>    on the CLI and the MCP server, so name a tool once for both.
> 2. **The Appcues MCP server's equivalent tools**, when there is no shell
>    or no binary.
> 3. **The [API v2](https://api.appcues.com/v2/docs) directly** as a last
>    resort.

Never *require* the CLI. Requirement 1 below says every skill must be
completable through MCP alone, so do not gate the skill on the binary
(e.g. no `metadata.openclaw.requires.bins: [appcues]`).

Two rules the access block implies, stated in every skill because agents
violate both in practice:

- **The tiers are an availability ladder, not a troubleshooting ladder.**
  Pick the first tier available and use it exclusively for the whole
  task. A failed or odd-looking call is never a reason to drop to a
  lower tier — read the structured error and act on it. (Observed: an
  agent with a working CLI reconstructed requests with curl because one
  output looked wrong, then spiraled.)
- **Never read, print, or hunt for credential files or secret values.**
  Credentials are ambient — the environment, or the CLI's own config,
  which the CLI reads itself. On an auth failure, stop and report what
  is missing. (Observed: the same spiral ended with the agent catting
  config files looking for raw keys.)

### Branching on CLI failure

The CLI fails loud and structured: non-zero exit, and exactly one JSON
line on stderr:

```json
{"error":true,"type":"auth","status":401,"message":"...","exit_code":3}
```

| exit | `type` | meaning | the skill should |
|---|---|---|---|
| 0 | | success | continue |
| 1 | `unexpected` | unknown failure | stop, report the message |
| 2 | `usage` | bad flags/arguments | fix the invocation, retry once |
| 3 | `config`, `auth` | missing or bad credentials | stop, report exactly what is needed |
| 4 | `api`, `tool` | API rejected the request (4xx), or a tool ran and reported failure (`isError`; the envelope is under `body`) | stop, report status + message |
| 5 | `rate_limited`, `server` | transient 429/5xx (already retried) | stop, report |

Data goes to stdout, everything else to stderr, so `-o json` output is
always parseable. Every write command supports `--dry-run`; use it to
verify a plan before mutating.

## The three requirements

Every skill must satisfy all three at once, because the flagship recipes
run on all three tiers:

1. **Completable through MCP alone.** Workspace agents (claude.ai chat,
   ChatGPT) have no shell, or no binary on PATH.
2. **Runnable unattended.** Never ask the user a question. On failure,
   stop and report exactly what failed and what is needed, as data (the
   error JSON, the missing variable name), not prose. On cron there is
   nobody to answer.
3. **Pleasant interactively.** A human at a terminal is the first user;
   keep output readable and say what you are doing.

A skill written against the coding tier alone fails silently on cron and
is unusable in a chat window.

## Output format is a MUST

If the skill produces a report, give a verbatim skeleton and demand it:
same sections, same order, same headings, explicit sorting. State empty
sections ("no segments"), never drop them. The skeleton is the contract,
not a suggestion; label it "(MUST)". This rule exists because it was
violated in practice: an agent regrouped a report thematically and
dropped the summary line when the format read as an example.

## Checklist for a new skill

- [ ] Frontmatter is spec-pure; `description` is trigger-only
- [ ] Access block copied; needs phrased as capabilities, not commands
- [ ] Completable via MCP alone; CLI never required
- [ ] Zero questions to the user; failures reported as structured data
- [ ] Output skeleton labeled MUST, with explicit sorting
- [ ] Writes guarded: read-only stated, or `--dry-run` verification step
- [ ] No runtime-isms, no cross-references; survives deleting `runtimes/`
