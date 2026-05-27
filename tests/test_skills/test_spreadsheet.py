from __future__ import annotations

from pathlib import Path

import pandas as pd


class TestSpreadsheetSkill:
    def test_load_csv(self, sample_csv: Path):
        import pandas as pd
        df = pd.read_csv(sample_csv)
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "department"]

    def test_convert_csv_to_xlsx(self, sample_csv: Path, mock_backend, sample_config):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry
        from unittest.mock import patch

        with patch("office_assistant.config.loader.load_config", return_value=sample_config):
            skill = SkillRegistry.get("spreadsheet")
            result = skill.execute(
                mock_backend,
                input_file=str(sample_csv),
                operation="convert",
                output_format="xlsx",
            )

            assert result.success
            assert len(result.files_generated) == 1
            assert result.files_generated[0].suffix == ".xlsx"

            # Clean up
            for f in result.files_generated:
                f.unlink(missing_ok=True)

    def test_analyze_csv(self, sample_csv: Path, mock_backend, sample_config):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry
        from unittest.mock import patch

        with patch("office_assistant.config.loader.load_config", return_value=sample_config):
            skill = SkillRegistry.get("spreadsheet")
            result = skill.execute(
                mock_backend,
                input_file=str(sample_csv),
                operation="analyze",
            )

            assert result.success
            assert "summary" in result.data
            assert result.data["summary"].row_count == 3
            assert result.data["summary"].column_count == 3

    def test_convert_nonexistent_file(self, mock_backend):
        import office_assistant.skills  # noqa: F401
        from office_assistant.core.skill_registry import SkillRegistry

        skill = SkillRegistry.get("spreadsheet")
        result = skill.execute(
            mock_backend,
            input_file="/nonexistent/file.csv",
            operation="convert",
            output_format="xlsx",
        )

        assert not result.success
        assert len(result.errors) > 0
