# Appcues skills

Portable [Agent Skills](https://agentskills.io) for working with an Appcues
account from an AI agent. One `skills/` directory, installable into Claude
Code, Codex, Hermes Agent, and OpenClaw with the thin manifests next to it.

The skills drive the [`appcues` CLI](https://github.com/appcues/cli) when a
shell and the binary are available, and fall back to the Appcues MCP server
or the API when they are not. Install the CLI first if your agent has a
shell; see the cli repo for instructions.

## The skills

| Skill | What it answers |
|---|---|
| `account-inventory` | What's in the account: flows, segments, tags, with counts |
| `analytics-query` | Analytics questions: usage over time, top events, filtered metrics, raw event exports |
| `weekly-performance-digest` | Weekly digest of published flows' performance: totals, top movers, completion regressions, vs the previous period |
| `experience-errors` | Error-rate spikes per experience plus step errors by flow, step, and error message vs the previous period; built for a daily scheduled run |
| `nps-sentiment` | One NPS survey's score trend plus themes and verbatim quotes from the written replies |
| `flow-step-dropoff` | Step-by-step funnel of one flow: where users are lost, with skip and error counts |
| `dashboard-digest` | Narrates an existing Appcues dashboard card by card: what each chart shows, the numbers, the change vs the previous window |
| `campaign-report` | One campaign end to end: objective, each tactic, its content with published state and engagement vs the previous period |

The authoring contract every skill follows is in [`skills/README.md`](skills/README.md).

## Install

### Claude Code

The repo is its own one-plugin marketplace. Send these as two separate prompts:

```
/plugin marketplace add appcues/skills
```

```
/plugin install appcues-skills@appcues
```

Pull new skill versions with `/plugin marketplace update appcues`.

### Codex

```bash
codex plugin marketplace add appcues/skills
```

Then run `codex`, open `/plugins`, and install **Appcues** from the
`appcues` marketplace. Start a new session; skills are invoked with `$`,
for example `$weekly-performance-digest`.

### Hermes Agent

Two routes from the same repo.

As a plugin, all eight skills at once:

```bash
hermes plugins install appcues/skills
```

The installer asks whether to enable the plugin; answer yes, or run
`hermes plugins enable appcues` later. After installing or reinstalling,
quit and reopen the Hermes desktop app (Cmd+Q, then relaunch): the app's
own backend loads plugins once per process, and `hermes gateway restart`
does not restart it.

Plugin skills are namespaced `appcues:<skill-name>` and reach the agent
through its `skills_list` tool, plus a note on the first turn of each
session listing them. Hermes does not show them in `hermes skills list`,
the dashboard Skills tab, or the system prompt index.

As a tap, one skill at a time, which does show up everywhere:

```bash
hermes skills tap add appcues/skills
hermes skills install appcues/skills/weekly-performance-digest
```

### OpenClaw

OpenClaw installs the repo as a plugin bundle and loads `skills/` as a skill root:

```bash
openclaw plugins install git:github.com/appcues/skills
openclaw gateway restart
```

Verify with `openclaw skills list`. For a local checkout, add its `skills/`
path to `skills.load.extraDirs` in `openclaw.json` instead.
