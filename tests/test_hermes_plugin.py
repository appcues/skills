"""Registration and catalog check for the Hermes plugin entry point. Run with an interpreter that has PyYAML, e.g. the Hermes venv:
~/.hermes/hermes-agent/venv/bin/python -m unittest tests/test_hermes_plugin.py"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO = Path(__file__).resolve().parent.parent


def _load_plugin():
    spec = importlib.util.spec_from_file_location("appcues_plugin", REPO / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StubCtx:
    def __init__(self):
        self.skills = {}
        self.hooks = {}

    def register_skill(self, name, path, description="", frontmatter=None):
        self.skills[name] = description

    def register_hook(self, hook_name, callback):
        self.hooks[hook_name] = callback


@unittest.skipUnless(yaml, "PyYAML required; run with the Hermes venv python")
class HermesPluginTest(unittest.TestCase):
    def test_registers_every_skill_and_advertises_them_on_the_first_turn(self):
        plugin = _load_plugin()
        ctx = StubCtx()

        plugin.register(ctx)

        expected = sorted(p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())
        self.assertEqual(sorted(ctx.skills), expected)
        self.assertTrue(all(ctx.skills.values()), "every skill should carry a description")

        hook = ctx.hooks["pre_llm_call"]
        first = hook(is_first_turn=True, session_id="s", user_message="hi", unexpected_kwarg=1)
        for name in expected:
            self.assertIn(f"appcues:{name}: ", first["context"])
        self.assertIn('skill_view("appcues:<skill-name>")', first["context"])
        self.assertTrue(all(len(line) < 200 for line in first["context"].splitlines()))
        self.assertIsNone(hook(is_first_turn=False))

    def test_malformed_frontmatter_skips_that_skill_only(self):
        plugin = _load_plugin()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "good").mkdir()
            (root / "good" / "SKILL.md").write_text("---\nname: good\ndescription: Fine.\n---\nbody\n")
            (root / "bad").mkdir()
            (root / "bad" / "SKILL.md").write_text("---\nname: [unclosed\n---\nbody\n")
            plugin.SKILLS_DIR = root
            ctx = StubCtx()

            with self.assertLogs(plugin.logger, level="WARNING"):
                plugin.register(ctx)

        self.assertEqual(list(ctx.skills), ["good"])
        self.assertIn("appcues:good", ctx.hooks["pre_llm_call"](is_first_turn=True)["context"])


if __name__ == "__main__":
    unittest.main()
