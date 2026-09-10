"""Hermes Agent plugin entry point.

Registers every skill under skills/ so Hermes exposes them as
appcues:<skill-name> via skills_list and skill_view, and advertises that
catalog to the model on the first turn of a session, because Hermes leaves
plugin skills out of the <available_skills> system-prompt index. Skill
content stays in the SKILL.md files; this file only points Hermes at them.
"""

import logging
from pathlib import Path

try:
    import yaml
except ImportError:  # Hermes ships PyYAML; without it skills register with no description
    yaml = None

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent / "skills"
_MAX_DESCRIPTION = 140


def _frontmatter(skill_md: Path):
    """Parse the YAML frontmatter of a SKILL.md. {} if absent, None if malformed."""
    text = skill_md.read_text(encoding="utf-8")
    if yaml is None or not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        logger.warning("Skipping %s: malformed frontmatter: %s", skill_md, exc)
        return None
    return data if isinstance(data, dict) else {}


def _trim(description: str) -> str:
    """First sentence, capped, so the catalog stays one line per skill."""
    first = description.strip().split(". ", 1)[0].rstrip(".")
    return first if len(first) <= _MAX_DESCRIPTION else first[: _MAX_DESCRIPTION - 1].rstrip() + "…"


def _catalog(skills) -> str:
    lines = [f"- appcues:{name}: {_trim(description)}" for name, description in skills]
    return (
        "Appcues skills installed in this session (not listed under available_skills):\n"
        + "\n".join(lines)
        + '\nWhen a request matches one, load it first with skill_view("appcues:<skill-name>").'
    )


def register(ctx):
    registered = []
    for child in sorted(SKILLS_DIR.iterdir()):
        skill_md = child / "SKILL.md"
        if not child.is_dir() or not skill_md.is_file():
            continue
        try:
            frontmatter = _frontmatter(skill_md)
            if frontmatter is None:
                continue
            description = str(frontmatter.get("description", ""))
            ctx.register_skill(child.name, skill_md, description=description, frontmatter=frontmatter)
        except Exception as exc:
            logger.warning("Skipping skill %s: %s", child.name, exc)
            continue
        registered.append((child.name, description))

    if not registered:
        return
    catalog = _catalog(registered)

    def advertise_skills(is_first_turn=True, **kwargs):
        # Injected into the user message, which stays in history, so once per session is enough.
        return {"context": catalog} if is_first_turn else None

    ctx.register_hook("pre_llm_call", advertise_skills)
