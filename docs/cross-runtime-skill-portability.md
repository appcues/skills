# Cross-runtime skills & plugins research (OpenClaw, Hermes, Claude Code, ChatGPT/Codex)

Research supporting the skill contract (skills/README.md). Researched 2026-08-20 from the official docs of each runtime; sources listed at the end.

## Headline

"Write once, use everywhere" for skills is real via the Agent Skills open standard (https://agentskills.io, open-sourced by Anthropic Dec 2025). All four runtimes implement it:

- Claude Code: originated it (code.claude.com/docs/en/skills).
- OpenAI ChatGPT + Codex: adopted it outright, byte-compatible SKILL.md; validation follows the spec (learn.chatgpt.com/docs/build-skills).
- OpenClaw: "follows the AgentSkills spec"; extensions namespaced under `metadata.openclaw` (docs.openclaw.ai/tools/skills).
- Hermes Agent: claims agentskills.io compatibility; extensions under `metadata.hermes`; installs skills from GitHub repos and raw SKILL.md URLs (hermes-agent.nousresearch.com/docs/user-guide/features/skills).

Portable core: directory + SKILL.md (YAML frontmatter + markdown body) + optional scripts/, references/, assets/. The spec allows exactly six frontmatter fields (name, description, license, compatibility, metadata, allowed-tools) and claude.ai/Skills-API hard-fail on anything else, so spec-purity is machine-enforceable.

## Feature table

| Capability | Claude Code | OpenClaw | Hermes | ChatGPT / Codex |
|---|---|---|---|---|
| SKILL.md (agentskills.io) | yes (origin) | yes | yes | yes (adopted) |
| Bundled scripts/references/assets | yes | yes ({baseDir}) | yes | yes |
| Invocation | /name + auto-trigger | /name + auto | /name + auto | $name + auto |
| Runtime-specific frontmatter | many extra fields (hard-fail elsewhere) | metadata.openclaw (requires.bins/env, os, install) | metadata.hermes + required_environment_variables, platforms, version | agents/openai.yaml companion file |
| Plugins | .claude-plugin/plugin.json + marketplaces | openclaw.plugin.json + ClawHub | Python plugins + taps/bundles | .codex-plugin/plugin.json + plugin directory (2026) |
| Hooks | yes | yes (HOOK.md + handler.ts) | yes | only bundled via plugins; none user-level in ChatGPT |
| MCP client | yes | yes | yes (also serves MCP) | yes (connectors/apps; Codex too) |
| Shell for skills | full host | exec (sandbox optional, off by default) | terminal (local/docker/ssh/cloud backends) | ChatGPT: sandboxed cloud container (bash+pip, no host); Codex: sandboxed local, network off by default |
| Scheduler (unattended) | routines (cloud) + desktop tasks + OS cron with `claude -p --bare` | built-in cron + webhooks + heartbeat | gateway cron, delivery to chat channels | ChatGPT automations (RRULE, cloud/desktop); Codex CLI: none |
| Per-skill configuration values | host settings and environment | per-skill entries in config; the sandbox does not receive them | required_environment_variables, forwarded to the sandbox | workspace policy / container |
| Distribution | marketplaces (/plugin install) | ClawHub | hub + `tap add owner/repo` + GitHub direct | workspace sharing, plugin directory, $skill-installer |

## Portability rules (what breaks)

Claude-Code-only features that must be avoided in portable skills: extra frontmatter (argument-hint, context: fork, hooks, paths, model, when_to_use, arguments, user-invocable, disable-model-invocation, disallowed-tools, effort, shell, agent, background) hard-errors on claude.ai/Skills-API upload; body features (!`command` injection, $ARGUMENTS/$N, ${CLAUDE_*} vars, @file refs) become literal text elsewhere. Hooks, subagents, and output styles are host features, not part of the format.

The real portability cliff is the binary, not the format: ChatGPT skills run in OpenAI's cloud Code Interpreter container, and Codex sandboxes are network-off by default, so the `appcues` CLI won't be on PATH there. This independently confirms the contract's requirement that every skill be completable through MCP (or raw API) alone, CLI preferred where a shell and binary exist.

## Recommended architecture for the Appcues skills

Layers:

- **L0, elementary tools**: the appcues CLI (peers: Appcues MCP server, raw API v2).
- **L1, the contract**: skills/README.md. Rules:
  1. Spec-pure frontmatter; runtime-specific needs go under metadata.<runtime> (e.g. metadata.openclaw.requires.bins: [appcues]).
  2. Capability-not-transport, with a canonical access block authors copy: prefer CLI (branch on typed exit codes 0-5, one JSON error line on stderr, -o json, --dry-run), fall back to MCP tools, last resort raw API.
  3. The three tier requirements: MCP-completable, unattended-safe, interactive-pleasant.
  4. MUST-level output formats with verbatim skeletons (fixes account-inventory's observed format drift).
  5. No runtime-isms in bodies.
  6. Skills are self-contained, never referencing each other's files.
- **L2, recipes**: skills/<purpose>/SKILL.md, composed purposes (account inventory, create experience, digest). Elementary knowledge (commands, payload shapes) lives in each skill's references/, not as separate skills.
- **Packaging (thin, per-runtime)**: plugin manifests at the root of this repo, all pointing at the same skills/, never inside the skill directories. On 2026-09-10 the skills moved here from appcues/cli, which keeps the CLI. Reason: Hermes scans every file under a plugin's install root before installing and a caution verdict blocks community installs, so a repo carrying CI, install docs, and shell scripts can never install cleanly as a plugin, while a tree of only plugin.json + skills/ scans safe. Shipped here: plugin.yaml + __init__.py (native Hermes plugin; install via hermes plugins install appcues/skills), plugin.json (Agent Plugins v1, the portable Codex manifest and Hermes fallback), .codex-plugin/plugin.json and .agents/plugins/marketplace.json (Codex marketplace), .claude-plugin/marketplace.json + plugin.json (the repo is its own one-plugin marketplace; install via /plugin marketplace add appcues/skills). OpenClaw needs no manifest: openclaw plugins install git:github.com/appcues/skills detects the bundle from the Codex and Claude markers. Hermes plugin skills are namespaced appcues:<skill>, visible through the agent's skills_list tool and a first-turn note the plugin injects, but not in hermes skills list, the dashboard, or the system prompt index; the tap route (hermes skills tap add appcues/skills) still works from the same layout and does show everywhere.
- **Scheduling stays out of skills**: "run the digest weekly" is one line of each runtime's own cron/automation config, so it belongs with the runtime sandboxes in appcues/cli's runtimes/, not in a skill.

Skip hooks, commands, and subagents entirely: not portable, not needed for recipes.

## Sources

docs.openclaw.ai (tools/skills, creating-skills, automation, clawhub, plugins/manifest, gateway/sandboxing); hermes-agent.nousresearch.com/docs (features/skills, plugins, hooks, cron, mcp, security, configuration, reference/cli-commands); code.claude.com/docs/en (skills, plugins, plugins-reference, plugin-marketplaces, hooks, sub-agents, mcp, memory, headless); learn.chatgpt.com/docs (build-skills, automations, plugins, sandboxing); developers.openai.com/api/docs/guides/tools-skills; agentskills.io/specification; github.com/openai/skills (archived, superseded by openai/plugins); third-party (labeled): simonwillison.net Dec 2025/Jan 2026 posts on OpenAI skills + ChatGPT containers.
