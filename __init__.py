"""Hermes Agent plugin entry point.

Registers every skill under skills/ so Hermes exposes them as
appcues:<skill-name> via skills_list and skill_view. Skill content stays in
the SKILL.md files; this file only points Hermes at them.
"""

from pathlib import Path

try:
    import yaml
except ImportError:  # Hermes ships PyYAML; without it skills register with no description
    yaml = None

SKILLS_DIR = Path(__file__).parent / "skills"


def _frontmatter(skill_md: Path) -> dict:
    """Parse the YAML frontmatter of a SKILL.md, or return {} if absent."""
    text = skill_md.read_text(encoding="utf-8")
    if yaml is None or not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1])
    return data if isinstance(data, dict) else {}


def register(ctx):
    for child in sorted(SKILLS_DIR.iterdir()):
        skill_md = child / "SKILL.md"
        if not child.is_dir() or not skill_md.is_file():
            continue
        frontmatter = _frontmatter(skill_md)
        ctx.register_skill(
            child.name,
            skill_md,
            description=str(frontmatter.get("description", "")),
            frontmatter=frontmatter,
        )
