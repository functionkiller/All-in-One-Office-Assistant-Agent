from __future__ import annotations

import json


class TestEmailSkill:
    def test_classify_email(self, mock_backend, sample_eml, sample_config):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry
        from unittest.mock import patch

        mock_backend.generate.return_value.content = json.dumps(
            {"category": "会议邀请", "confidence": 0.95, "summary": "关于Q2路线图的会议", "urgency": "high"},
            ensure_ascii=False,
        )

        with patch("office_assistant.config.loader.load_config", return_value=sample_config):
            skill = SkillRegistry.get("email")
            result = skill.execute(
                mock_backend,
                input_file=str(sample_eml),
                operation="classify",
            )

            assert result.success
            assert result.data["classification"].category == "会议邀请"
            assert result.data["classification"].urgency == "high"

    def test_invalid_file(self, mock_backend):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("email")
        result = skill.execute(mock_backend, input_file="/nonexistent/email.eml")

        assert not result.success
        assert len(result.errors) > 0

    def test_skill_registered(self):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("email")
        assert skill is not None
        assert skill.name == "email"
        assert "input_file" in skill.required_inputs
