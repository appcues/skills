# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Nine portable Agent Skills (`skills/<name>/SKILL.md`): eight that report on an Appcues account plus `appcues-cli`, the operational fallback for ad hoc CLI tasks, plus thin per-runtime manifests at the root so one tree installs into Claude Code, Codex, Hermes Agent, and OpenClaw. The layout mirrors anthropics/skills: everything of substance lives in `skills/`, and every manifest points at that same directory. There is no build and no dependency install; one stdlib unittest for the Hermes plugin plus the checks below are the whole verification story.

The skills themselves are authored against the contract in `skills/README.md` (spec-pure frontmatter, capability-not-transport access block, MUST-level output skeletons, no runtime-isms, no cross-references between skills). Read it before editing or adding a skill. The skills originated in appcues/cli and were moved here; that repo still holds the CLI the skills drive.

## Layout

```
skills/<name>/SKILL.md            the skills; references/ where a skill needs sample payloads
skills/README.md                  the authoring contract
plugin.json                       Agent Plugins v1 manifest: Hermes, Codex (portable), OpenClaw bundle
.claude-plugin/                   Claude Code marketplace + plugin manifest
.codex-plugin/plugin.json         Codex presentation metadata (compatibility overlay)
.agents/plugins/marketplace.json  Codex marketplace
plugin.yaml + __init__.py         Hermes native plugin: registers skills/ as appcues:<name>, first-turn catalog hook
tests/test_hermes_plugin.py       stub-ctx check for the plugin; needs PyYAML, see Verification
AGENTS.md                         pointer to this file for other agents
docs/install.md                   the one end-to-end install guide (runtime, CLI, key, skills, first check)
docs/*.md                         packaging research: cross-runtime portability, skill ecosystem survey
```

Every manifest points at the same `skills/` directory. Nothing runtime specific lives inside a skill.

## Manifests and what reads them

| File | Read by |
|---|---|
| `plugin.yaml` + `__init__.py` | Hermes native plugin (`hermes plugins install`); preferred over `plugin.json` when both exist |
| `plugin.json` | Codex (portable root manifest), OpenClaw (Agent Plugins bundle marker), Hermes fallback |
| `.codex-plugin/plugin.json` | Older Codex builds as a compatibility overlay; supplies the `interface` display block. Also an OpenClaw bundle marker |
| `.agents/plugins/marketplace.json` | `codex plugin marketplace add appcues/skills` |
| `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json` | `/plugin marketplace add appcues/skills` (the repo is its own one-plugin marketplace, source `./`) |

Hermes taps (`hermes skills tap add appcues/skills`) and OpenClaw's `extraDirs` route need no manifest at all; they work off the `skills/` layout.

Versions are duplicated: `plugin.yaml`, `plugin.json`, and `.codex-plugin/plugin.json` carry the plugin version, `.claude-plugin/plugin.json` has its own. Bump them together.

The Codex marketplace entry uses a `url` source pointing at the repo's own git URL, not a local `./` path. Codex silently skips a local `./` entry when the plugin is the marketplace root, so that is not a mistake to fix.

## Constraints on what may live in the repo

Hermes runs a security scan over every file at the install root before installing, and a caution verdict blocks community installs. Docs, CI workflows, and shell scripts are the usual triggers. Keep the top level to manifests, the Hermes plugin entry point, README, AGENTS.md, docs/, and this file; do not add workflows, scripts, or prose that reads like install instructions piping remote content into a shell. Run the scan after any change outside `skills/`.

Each `SKILL.md` frontmatter `name` must equal its folder name and its `description` must stay under 1024 characters, or Hermes rejects the package.

## Verification commands

Hermes scan and manifest load (Hermes source checkout under `~/.hermes/hermes-agent`):

```bash
~/.hermes/hermes-agent/venv/bin/python -c "
import sys, tempfile; from pathlib import Path
sys.path.insert(0, str(Path.home() / '.hermes/hermes-agent'))
from tools.plugin_guard import scan_plugin
from hermes_cli.agent_plugins import load_agent_plugin
r = scan_plugin(Path('.').resolve()); print(r.verdict, len(r.findings), [str(f) for f in r.findings])
p = load_agent_plugin(Path('.').resolve(), Path(tempfile.mkdtemp())); print(sorted(s.name for s in p.skills))"
hermes plugins validate .
```

Expected: verdict `safe` and all nine skill names. The standing findings are low, informational `agent_config_ref` hits wherever this file or AGENTS.md is named; they do not affect the verdict, so do not chase them. Anything with another pattern id is new.

Claude Code and Codex:

```bash
~/.hermes/hermes-agent/venv/bin/python -m unittest tests/test_hermes_plugin.py
hermes plugins doctor . --ci
claude plugin validate .
codex plugin marketplace add .          # marketplace loads; the url entry only resolves against GitHub
codex plugin marketplace remove appcues
```

To exercise the Codex install end to end without pushing, commit a scratch copy of the repo to a temporary git directory, point a scratch marketplace's `url` at it with `file://`, then `codex plugin add appcues@<marketplace>` and check `~/.codex/plugins/cache/<marketplace>/appcues/<version>/skills/`. Remove the plugin, the marketplace, and that cache directory afterwards.

OpenClaw is not installed on the development machine; its section of the README is from docs.openclaw.ai (plugin bundles page) and has not been run.
