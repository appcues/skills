# Skill ecosystem survey: which agentic systems popular skill repos support

Empirical companion to [cross-runtime-skill-portability.md](cross-runtime-skill-portability.md):
that doc covers what the specs allow, this one covers what popular repos
actually ship. Surveyed 2026-08-26 from a "17 skills" roundup; repo
identities and star counts verified against the GitHub API, then each
repo's README, install docs, and directory layout were analyzed for
declared runtime support.

## Verified repo list

Confidence: green = identity and stars confirmed, yellow = probable match
with a caveat.

| # | Tool | Repo | Stars | Confidence |
|---|------|------|------:|:----------:|
| 1 | Agent-Reach | https://github.com/Panniantong/Agent-Reach | 75,463 | green |
| 2 | make-interfaces-feel-better | https://github.com/jakubkrehel/make-interfaces-feel-better | 3,019 | green |
| 3 | oh-my-hermes | https://github.com/witt3rd/oh-my-hermes | 289 | green |
| 4 | Anthropic Cybersecurity Skills | https://github.com/mukul975/Anthropic-Cybersecurity-Skills | 31,181 | green (community repo, not by Anthropic) |
| 5 | OpenMontage | https://github.com/calesthio/OpenMontage | 50,589 | green |
| 6 | Minions | https://github.com/agent37-platform/minions | 624 | green |
| 7 | Resemble Detect | https://github.com/resemble-ai/detect-skill | 64 | green |
| 8 | agent-skills | https://github.com/addyosmani/agent-skills | 89,900 | green |
| 9 | Composio skills | https://github.com/ComposioHQ/composio | 29,886 | yellow (ecosystem main repo, exact skills repo ambiguous) |
| 10 | youtube-full | https://github.com/ZeroPointRepo/youtube-skills | 567 | yellow (no repo named youtube-full; description and stars match) |
| 11 | Humanizer | https://github.com/blader/humanizer | 37,987 | green |
| 12 | Defuddle | https://github.com/kepano/defuddle | 9,161 | green |
| 13 | Matt Pocock skills | https://github.com/mattpocock/skills | 237,459 | green |
| 14 | SkillClaw | https://github.com/AMAP-ML/SkillClaw | 2,511 | green |
| 15 | Browser Harness | https://github.com/browser-use/browser-harness | 17,147 | green |
| 16 | codebase-memory-mcp | https://github.com/DeusData/codebase-memory-mcp | 40,711 | green |
| 17 | Loopy / Loop Library | https://github.com/Forward-Future/loopy | 3,062 | green |

## Runtime support matrix (green repos)

Defuddle turned out to be a plain TypeScript library/CLI, not a skill
(the skill wrapper is the separate `joeseesun/defuddle-skill`), so it is
marked N/A.

| Repo | Type | Claude Code | Hermes | OpenClaw | Codex | Cursor | Windsurf | Copilot | Gemini CLI | Others |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| Agent-Reach | CLI + MCP | yes | | yes | | yes | yes | | | "any agent that can run a shell" |
| make-interfaces-feel-better | SKILL.md | yes | | | | | | | | generic via AGENTS.md |
| oh-my-hermes | Hermes plugins | | yes | | | | | | | Hermes-only |
| Anthropic Cybersecurity Skills | skills/ + plugin | yes | yes | | yes | yes | yes | yes | yes | Cline, Roo, Zed, Droid |
| OpenMontage | skills + per-agent configs | yes | | | yes | yes | yes | yes | | ships .claude, .codex, .cursor, .windsurfrules, .agents |
| Minions | app on top of Hermes | | yes | planned | | | | | | Hermes-only, OpenClaw adapter "next" |
| Resemble Detect | single SKILL.md | yes | yes | yes | | yes | yes | yes | yes | "any agent that supports markdown skills" |
| agent-skills (addyosmani) | skills + plugins | yes | | | yes | yes | yes | yes | yes | OpenCode, Kiro, Antigravity, Cline, Zed |
| Humanizer | SKILL.md + CC plugin | yes | | | | | | | | generic via AGENTS.md |
| Matt Pocock skills | skills/ + CC plugin | yes | | | yes | | | | | generic .agents dir |
| SkillClaw | proxy/evolve server | yes | yes | yes | yes | | | | | QwenPaw, IronClaw, PicoClaw, ZeroClaw, any OpenAI-compatible API |
| Browser Harness | CC plugin + SKILL.md | yes | | | yes | | | | | |
| codebase-memory-mcp | MCP server | yes | yes | yes | yes | yes | yes | yes | yes | any MCP client (Cline, Goose, Zed, Kiro, Trae, ...) |
| Loopy | skills + loop library | yes | | | yes | yes | | | | Zed, generic AGENTS.md |
| Defuddle | JS library | N/A | | | | | | | | not a skill; agent wrapper is a separate repo |

## Ranking: most-supported runtimes across these repos

| Rank | System | Repos | Note |
|---|---|:-:|---|
| 1 | Claude Code | 12 of 14 | The de facto baseline: everything except the two Hermes-native apps targets it, and SKILL.md is the lingua franca even in non-Claude repos |
| 2 | Codex | 8 | Almost always second on the list, usually via the same skill files |
| 3 | Cursor | 7 | Via .cursor/skills/ or project rules, rarely dedicated content |
| 4 | Hermes | 6 | Includes the deepest integrations (oh-my-hermes, Minions, SkillClaw are Hermes-native) plus the broad-coverage repos |
| 4 | Windsurf | 6 | Same pattern as Cursor: project rules pointing at shared markdown |
| 6 | Copilot | 5 | Via copilot-instructions.md |
| 7 | OpenClaw | 4 | 5 counting Minions' planned adapter; growing, imports markdown skills directly |
| 7 | Gemini CLI | 4 | .gemini/skills/ |
| - | Long tail | 1-4 each | Zed (4), Cline (3), OpenCode, Kiro, Antigravity, Roo, Goose, QwenPaw, Trae, Droid |

## Who offers MCP

Only one green repo is MCP-first; the rest either touch MCP as a
side-channel or not at all.

| Repo | MCP? | How |
|---|---|---|
| codebase-memory-mcp | Yes, MCP-only | It IS an MCP server, that is its entire interface (any MCP client connects) |
| Composio (yellow) | Yes | The platform's whole business is hosted MCP servers and tool auth |
| Resemble Detect | Optional side-channel | The skill uses plain REST via curl and explicitly says agents "do not need an MCP server"; a hosted mcp.resemble.ai exists only for docs/schema lookup |
| Agent-Reach | Consumes, doesn't offer | A CLI that wraps third-party MCP servers (xiaohongshu-mcp, linkedin-mcp, Exa via mcporter) as backends behind its own commands |
| The other 11 | No | Pure markdown skills, plugins, or apps; MCP appears only as topic content |

MCP shows up in exactly three roles across the set:

1. **The product itself** (codebase-memory-mcp): justified because a
   persistent code-graph index is a stateful server, not something to
   re-run per CLI invocation.
2. **An optional docs endpoint** (Resemble): the executable path stays
   REST/CLI, MCP is a convenience layer marked as not required.
3. **Hidden behind a CLI** (Agent-Reach): the skill-facing interface is
   shell commands, MCP is plumbing.

Nobody in this set ships a CLI and a parallel MCP interface for the same
commands. Since the appcues CLI is stateless request/response (unlike
the code-graph case), this reinforces the repo's stance: skills + CLI
now, MCP only if a non-shell consumer materializes.

## Portability patterns observed

Three patterns, in order of leverage:

1. **The skill IS a markdown file; everything else is packaging.** The
   most portable repos (Resemble Detect, addyosmani, cybersecurity
   skills) keep all knowledge in plain SKILL.md files with no
   system-specific syntax, then support each system through its
   discovery mechanism only: .claude/skills/, .cursor/skills/,
   .gemini/skills/, project rules, copilot-instructions.md. Resemble
   Detect covers 7 systems with one SKILL.md and an install table.
2. **AGENTS.md as the neutral entry point, CLAUDE.md pointing at it.**
   Nearly every multi-system repo does this; per-system files
   (OpenMontage's CODEX.md, CURSOR.md) exist but are thin pointers.
3. **Shell out to a CLI for anything executable.** Agent-Reach's
   compatibility claim is "Claude Code, OpenClaw, Cursor, Windsurf...
   any agent that can run a command line", with MCP as a secondary
   transport. This validates the Appcues CLI + skills architecture: the
   CLI is the portable capability layer, the SKILL.md tells any agent
   how to drive it.

Recipe confirmed for this repo's skills: plain SKILL.md assuming only
"can run shell commands", AGENTS.md entry point, no runtime-specific
references in skill bodies (delete appcues/cli's runtimes/ and every skill still describes complete work), per-system
install instructions as documentation, not code. Targeting Claude Code +
Codex + Hermes/OpenClaw explicitly covers the whole observed market. See
[cross-runtime-skill-portability.md](cross-runtime-skill-portability.md)
for the spec-level rules this survey confirms empirically.

## Distribution channels: how skills get listed

Researched 2026-08-26 from the ClawHub and Hermes docs. Both channels
are low-friction and this repo's `skills/<name>/SKILL.md` layout is
already the correct shape for both.

### ClawHub (clawhub.ai), the OpenClaw registry

Official OpenClaw skill + plugin registry
([openclaw/clawhub](https://github.com/openclaw/clawhub)). Small as of
this survey (roughly 30 skills, 12 plugins, download counts under ~200),
so early listings stand out. Sections: Trending / Featured / Official /
New plus use-case groupings.

Listing is self-service via CLI, with automated review:

```bash
npm i -g clawhub
clawhub login
clawhub skill publish ./my-skill --slug my-skill --name "My Skill"
```

- Publish-time validation (metadata, name, version, files, source),
  then automated security checks; a release stays hidden from
  install/search surfaces until review finishes.
- Up to 3 categories (fixed slug list) + 5 free-form topics; reserved
  topics ("official", "verified", "certified") are rejected, those
  labels are curation-only. Official/Featured are curated by the
  OpenClaw team (criteria unpublished); Trending is download-driven.
- Versioning is automatic: first release 1.0.0, auto-patch on changes.
- A reusable `skill-publish.yml` GitHub Action publishes every skill
  under a repo's `skills/` directory, which matches this repo exactly.
- Plugins additionally need `openclaw.plugin.json`, a scoped package
  name, and support OIDC trusted publishing from GitHub Actions.

Docs: https://docs.openclaw.ai/clawhub/publishing

### Hermes Skills Hub, decentralized

No registry sign-up at all:

- A **tap** is any GitHub repo with a `skills/` directory of SKILL.md
  folders. Once this repo is public, `hermes skills tap add appcues/skills`
  works with zero action on our side.
- Hub **search** aggregates: official `optional-skills/` in the Hermes
  repo, default taps (OpenAI, Anthropic, HuggingFace, NVIDIA), skills.sh
  (Vercel's directory), sites publishing
  `/.well-known/skills/index.json`, and community marketplaces
  **including ClawHub**. One ClawHub publish therefore also makes a
  skill discoverable inside Hermes.
- `hermes skills publish skills/my-skill --to github --repo owner/repo`
  is sugar for pushing to a tap repo.
- Trust levels: `builtin` for official skills, `community` for the
  rest; all hub installs pass a security scanner (exfiltration, prompt
  injection, destructive commands).

Docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/

### Order of operations when this repo goes public

1. Public repo: Hermes taps and `npx skills add` work immediately.
2. `clawhub skill publish` (or the GitHub Action): ClawHub listing,
   which also feeds Hermes hub search.
3. Optionally publish `/.well-known/skills/index.json` on an Appcues
   domain for the well-known discovery convention.

Nothing is published until explicitly decided; this section is the map,
not the trigger.
