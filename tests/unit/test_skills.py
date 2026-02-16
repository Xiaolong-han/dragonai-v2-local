
import pytest
from unittest.mock import patch, MagicMock
from app.skills.definitions import SKILLS, Skill
from app.skills.loader_tool import load_skill


class TestSkillDefinitions:
    def test_skills_type(self):
        assert isinstance(SKILLS, list)
        assert len(SKILLS) > 0
        for skill in SKILLS:
            assert isinstance(skill, dict)
            assert "name" in skill
            assert "description" in skill
            assert "content" in skill

    def test_skill_names(self):
        skill_names = [s["name"] for s in SKILLS]
        assert "image_generation" in skill_names
        assert "image_editing" in skill_names
        assert "coding" in skill_names
        assert "translation" in skill_names

    def test_skill_descriptions_not_empty(self):
        for skill in SKILLS:
            assert len(skill["description"]) > 0
            assert len(skill["content"]) > 0


class TestLoadSkillTool:
    def test_load_skill_exists(self):
        result = load_skill.func("coding")
        assert result is not None
        assert "coding" in result

    def test_load_skill_not_exists(self):
        result = load_skill.func("nonexistent_skill")
        assert "not found" in result.lower()

    def test_load_skill_image_generation(self):
        result = load_skill.func("image_generation")
        assert "Image Generation Skill" in result

