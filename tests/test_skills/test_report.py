from __future__ import annotations


class TestReportWritingSkill:
    def test_generate_weekly_report(self, mock_backend, sample_config):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry
        from unittest.mock import patch

        mock_backend.generate.return_value.content = (
            "# 本周工作摘要\n本周完成了核心模块开发。\n\n"
            "# 主要成果\n- 登录模块上线\n- 修复3个bug\n\n"
            "# 遇到的问题\n- 性能优化需要进一步处理\n\n"
            "# 下周计划\n- 开始数据迁移"
        )

        with patch("office_assistant.config.loader.load_config", return_value=sample_config):
            skill = SkillRegistry.get("report")
            result = skill.execute(
                mock_backend,
                content="完成了登录模块、修复了3个bug、开始数据迁移准备工作",
                report_type="weekly",
                style="professional",
            )

            assert result.success
            assert result.data["report"].raw_text
            assert len(result.files_generated) == 1
            assert result.files_generated[0].suffix == ".md"

            # Clean up
            for f in result.files_generated:
                f.unlink(missing_ok=True)

    def test_parse_sections(self):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("report")
        sections = skill._parse_sections(
            "# 标题\n内容段落\n\n## 第一节\n第一节内容\n\n## 第二节\n第二节内容"
        )
        assert len(sections) >= 1
