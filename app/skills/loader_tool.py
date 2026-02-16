from langchain.tools import tool

from app.skills.definitions import SKILLS


_skills_cache = None


def refresh_skills() -> None:
    """Refresh the skills cache. Call this when skills are updated."""
    global _skills_cache
    _skills_cache = None


def _get_skills() -> list:
    """Get the skills list, using cache if available."""
    global _skills_cache
    if _skills_cache is None:
        _skills_cache = SKILLS
    return _skills_cache


@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "image_generation", "coding", "translation")
    """
    skills = _get_skills()

    for skill in skills:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    available = ", ".join(s["name"] for s in skills)
    return f"Skill '{skill_name}' not found. Available skills: {available}"
