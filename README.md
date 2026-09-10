# Appcues skills

Portable [Agent Skills](https://agentskills.io) for working with an Appcues
account from an AI agent. One `skills/` directory, installable into Claude
Code, Codex, Hermes Agent, and OpenClaw with the thin manifests next to it.

The skills drive the [`appcues` CLI](https://github.com/appcues/cli) when a
shell and the binary are available, and fall back to the Appcues MCP server
or the API when they are not.

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

The skills need the [`appcues` CLI](https://github.com/appcues/cli) and an
Appcues API key on the machine the agent runs on. The full procedure, from
runtime install to a first check, is in [docs/install.md](docs/install.md).
The skills-only step per runtime:

| Runtime | Command |
|---|---|
| Claude Code | `/plugin marketplace add appcues/skills`, then `/plugin install appcues-skills@appcues` |
| Codex | `codex plugin marketplace add appcues/skills`, then install from `/plugins` |
| Hermes Agent | `hermes plugins install appcues/skills`, then `hermes gateway restart` and relaunch the desktop app |
| OpenClaw | `openclaw plugins install git:github.com/appcues/skills`, then `openclaw gateway restart` |
