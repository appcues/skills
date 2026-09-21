# Installing the Appcues skills

Set up an agent runtime, give it the `appcues` CLI, and install the skills. Steps 2 to 4 are the same for every runtime; steps 1 and 5 have a subsection per runtime. This guide is for using the skills, not writing them.

**Your Appcues account needs MCP access enabled.** The CLI's `appcues tools` commands, and the skills that use them (NPS sentiment today), need MCP access on the account. Without it those commands return an authorization error even with a valid key. Ask Appcues support to enable MCP for the account if `appcues tools list` fails after step 4.

Four things to know first:

1. **Access is bounded by the API key's role.** The agent can only do what the key you give it allows. Create a key with the least role that covers the skills you plan to run; read-only covers every skill in the catalog. Revoke it from Studio when done.
2. **The agent runs on your computer as you**, with your shell and your files. Hermes runs commands without asking; Claude Code and Codex ask first by default. Point any of them at a demo or sandbox account first.
3. **Prefer a subscription over a pay-per-token API key for the model.** Claude Code signs in with a Claude Pro or Max subscription; Hermes with a Claude Max subscription (extra usage credits; Pro is not supported) or a ChatGPT subscription; Codex with a ChatGPT subscription. A raw provider API key has no spending ceiling, and an unattended agent can run it up.
4. **Containers are safer.** Hermes and OpenClaw both ship Docker images that confine the agent to bind mounts. Use one if you can.

## 1. Install the runtime

Follow the runtime's own install page, then sign in with a subscription account:

| Runtime | Install | State lives in |
|---|---|---|
| [Hermes Agent](https://hermes-agent.nousresearch.com) | Website installer, then `hermes model` to pick the provider and `hermes status` to confirm | `~/.hermes/` |
| [Claude Code](https://code.claude.com) | `brew install --cask claude-code`, then `claude` opens the browser sign-in | `~/.claude/` |
| [Codex](https://developers.openai.com/codex) | Docs quick start, then `codex` signs in | `~/.codex/` |
| [OpenClaw](https://docs.openclaw.ai) | Docs quick start; the gateway refuses to start unconfigured | `~/.openclaw/` |

Hermes has three front ends over one agent, so everything below applies to all of them: the CLI/TUI (`hermes`), the web dashboard (`hermes dashboard`), and the desktop app (`hermes desktop`, or the installed app).

## 2. Install the `appcues` CLI

With Homebrew on macOS or Linux:

```bash
brew install appcues/tap/appcues
appcues --version
```

Upgrade later with `brew upgrade appcues`.

**Without Homebrew**, download the tarball for your platform from the [appcues/cli releases page](https://github.com/appcues/cli/releases) (`aarch64-apple-darwin`, `x86_64-apple-darwin`, `aarch64-unknown-linux-gnu`, or `x86_64-unknown-linux-gnu`), extract the binary, and put it on your PATH:

```bash
gh release download -R appcues/cli -p 'appcues-aarch64-apple-darwin.tar.xz'
tar -xf appcues-aarch64-apple-darwin.tar.xz --strip-components=1 '*/appcues'
mkdir -p ~/.local/bin && install -m 755 appcues ~/.local/bin/
appcues --version
```

The macOS binary is unsigned, so Gatekeeper quarantines browser downloads; the [appcues/cli README](https://github.com/appcues/cli#install) covers clearing that flag and building from source.

Whichever route you take, the binary's directory must be on the PATH of whatever shell the runtime spawns; see the first-check notes in step 6 if a runtime cannot find it.

## 3. Create Appcues API credentials

In Appcues Studio open [Settings, API keys](https://studio.appcues.com/settings/keys) and create a key. Note the key, the secret, and your account ID. Pick the least role that covers what you want the skills to do.

## 4. Save a profile

```bash
appcues profiles add            # prompts for key, secret, account ID, and env (prod, or prod-eu for EU accounts)
appcues status                  # Account <id> via https://api.appcues.com: credentials OK
```

The profile is written to the CLI's own config file, readable only by you. Every runtime runs as your user, so they all read the same profile; nothing else needs configuring.

## 5. Install the skills

Every route below installs from this repo and clones it with your local git credentials.

### Hermes Agent

All eight skills arrive as one plugin. The installer asks whether to enable it; say yes (or run `hermes plugins enable appcues` later). Then restart **both** processes that load plugins:

```bash
hermes plugins install appcues/skills
hermes gateway restart
```

and, if you use the desktop app, quit it with Cmd+Q and reopen it. Each process loads plugins once at start: the gateway restart does not reach the desktop app's own backend, and relaunching the app does not restart the gateway. Both restarts apply after every reinstall. The desktop app can also do the install from Capabilities, Plugins, Install from Git, with `https://github.com/appcues/skills` as the URL.

Plugin skills are namespaced `appcues:<skill-name>`. The agent finds them through its `skills_list` tool, and the plugin lists them in a note on the first turn of each session. They do not appear in `hermes skills list`, the dashboard Skills tab, or the system prompt index; that is how Hermes treats every plugin's skills.

If you would rather see them in `hermes skills list`, install them one at a time as a tap instead:

```bash
hermes skills tap add appcues/skills
hermes skills install appcues/skills/account-inventory --yes
```

### Claude Code

The repo is its own one-plugin marketplace. Inside a `claude` session, as two separate prompts:

```
/plugin marketplace add appcues/skills
```

```
/plugin install appcues-skills@appcues
```

Updates are not automatic: `/plugin marketplace update appcues` pulls new skill versions.

### Codex

```bash
codex plugin marketplace add appcues/skills
```

Then run `codex`, open `/plugins`, and install **Appcues** from the `appcues` marketplace. Start a new session; skills are invoked with `$`, for example `$weekly-performance-digest`. The IDE extension does not support plugins.

### OpenClaw

OpenClaw installs the repo as a plugin bundle and loads `skills/` as a skill root:

```bash
openclaw plugins install git:github.com/appcues/skills
openclaw gateway restart
```

Verify with `openclaw skills list`. For a local checkout, add its `skills/` path to `skills.load.extraDirs` in `openclaw.json` instead.

## 6. Run a first check

Start the runtime and ask: `Run appcues status and tell me what it says.` The agent should run the command and report the same `credentials OK` line from step 4. Then try a skill: `Give me an inventory of the account.`

If the agent reports `appcues: command not found`, its shell did not inherit your PATH. Confirm `which appcues` works in a fresh terminal, then start a new session. The Hermes desktop app launched from the Dock gets only the login-shell PATH, not the interactive one; either start it with `hermes desktop` from a terminal, or add the binary's directory (Homebrew's `bin`, or `~/.local/bin` for a tarball install) to the PATH in your login-shell profile as well. Claude Code and Codex inherit the shell they were launched from.
