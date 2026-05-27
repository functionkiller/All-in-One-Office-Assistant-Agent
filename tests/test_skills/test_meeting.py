from __future__ import annotations

import json

from office_assistant.models.meeting import MeetingMinutes, TodoItem


class TestMeetingMinutesSkill:
    def test_extract_todos_from_json(self, mock_backend):
        mock_backend.generate.return_value.content = json.dumps(
            [
                {"task": "更新Q2路线图", "assignee": "张三", "deadline": "周五", "priority": "high"},
                {"task": "回复客户邮件", "assignee": "李四", "deadline": "周三", "priority": "medium"},
            ],
            ensure_ascii=False,
        )

        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("meeting")
        minutes = MeetingMinutes(
            title="Q2 Planning",
            notes="会议记录内容...",
        )
        todos = skill._extract_todos(mock_backend, minutes)

        assert len(todos) == 2
        assert todos[0].task == "更新Q2路线图"
        assert todos[0].assignee == "张三"
        assert todos[0].priority == "high"

    def test_skill_has_required_inputs(self):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("meeting")
        assert skill is not None
        assert "audio_file" in skill.required_inputs
        assert skill.name == "meeting"

    def test_missing_audio_file(self, mock_backend):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("meeting")
        result = skill.execute(mock_backend, audio_file="/nonexistent/audio.mp3")

        assert not result.success
        assert any("不存在" in e for e in result.errors)
