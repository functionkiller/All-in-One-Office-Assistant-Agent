from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import Message
from office_assistant.core.skill_registry import SkillRegistry
from office_assistant.core.skill_result import SkillResult


class RouterResult(BaseModel):
    skill: str
    confidence: float
    parameters: dict[str, Any] = {}
    clarification_needed: bool = False
    clarification_question: str = ""


ROUTER_SYSTEM_PROMPT = """You are an intent classifier for an all-in-one office assistant agent. Your job is to understand the user's request and route it to the correct skill.

Available skills:
{skill_descriptions}

Analyze the user's request and output ONLY a JSON object (no other text) with these fields:
- "skill": the name of the most appropriate skill
- "confidence": a number from 0.0 to 1.0 indicating your confidence
- "parameters": extracted key-value parameters (e.g., file paths, operation type, language)
- "clarification_needed": true if the request is ambiguous and needs more detail
- "clarification_question": if clarification is needed, the question to ask (otherwise empty string)

Output ONLY valid JSON. No explanation, no markdown."""


class AgentRouter:
    def __init__(self, backend: LLMBackend):
        self.backend = backend

    def route(self, user_input: str) -> RouterResult:
        skill_context = SkillRegistry.get_router_context()
        system_prompt = ROUTER_SYSTEM_PROMPT.format(skill_descriptions=skill_context)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_input),
        ]

        response = self.backend.generate(
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )

        return self._parse_response(response.content)

    def dispatch(self, result: RouterResult) -> SkillResult:
        skill = SkillRegistry.get(result.skill)
        if skill is None:
            available = [s.name for s in SkillRegistry.list_all()]
            return SkillResult(
                success=False,
                skill_name=result.skill,
                errors=[f"Skill '{result.skill}' not found. Available: {', '.join(available)}"],
            )

        try:
            skill.validate_input(**result.parameters)
        except ValueError as e:
            return SkillResult(
                success=False,
                skill_name=result.skill,
                errors=[str(e)],
            )

        return skill.execute(self.backend, **result.parameters)

    def ask(self, user_input: str) -> SkillResult:
        """Route and dispatch in one call. The main entry point for natural language."""
        route_result = self.route(user_input)

        if route_result.clarification_needed:
            return SkillResult(
                success=False,
                skill_name=route_result.skill,
                text_output=route_result.clarification_question,
                errors=[f"需要更多信息: {route_result.clarification_question}"],
            )

        return self.dispatch(route_result)

    def _parse_response(self, text: str) -> RouterResult:
        # Extract JSON from potential markdown code blocks
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            text = json_match.group(0)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return RouterResult(
                skill="",
                confidence=0.0,
                clarification_needed=True,
                clarification_question="无法理解您的请求，请更具体地描述您的需求。",
            )

        return RouterResult(
            skill=data.get("skill", ""),
            confidence=float(data.get("confidence", 0.0)),
            parameters=data.get("parameters", {}),
            clarification_needed=data.get("clarification_needed", False),
            clarification_question=data.get("clarification_question", ""),
        )
