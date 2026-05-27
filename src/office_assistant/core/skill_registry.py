from __future__ import annotations

from typing import Type

from office_assistant.core.skill_base import BaseSkill


class SkillRegistry:
    _skills: dict[str, BaseSkill] = {}

    @classmethod
    def register(cls, skill: BaseSkill) -> None:
        cls._skills[skill.name] = skill

    @classmethod
    def get(cls, name: str) -> BaseSkill | None:
        return cls._skills.get(name)

    @classmethod
    def list_all(cls) -> list[BaseSkill]:
        return list(cls._skills.values())

    @classmethod
    def get_router_context(cls) -> str:
        """Generate a description of all registered skills for the router prompt."""
        lines = []
        for skill in cls._skills.values():
            lines.append(f"- **{skill.name}**: {skill.description}")
            if skill.required_inputs:
                params = ", ".join(
                    f"{k} ({v.get('type', 'str')})"
                    for k, v in skill.required_inputs.items()
                )
                lines.append(f"  Required inputs: {params}")
        return "\n".join(lines)


def register_skill(cls: Type[BaseSkill]):
    """Class decorator that instantiates and registers a skill."""
    instance = cls()
    SkillRegistry.register(instance)
    return cls
