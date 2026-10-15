import json
from typing import Any

import httpx
from app.integrations.llm.base import LLMProvider
from app.schemas.agent import StructuredGoalParsingOutput


class GeminiProvider(LLMProvider):
    """Google Gemini API Provider for real LLM inference with structured JSON schemas."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    async def parse_and_decompose_goal(
        self,
        goal_prompt: str,
        current_time_iso: str,
        user_context: dict[str, Any],
    ) -> StructuredGoalParsingOutput:
        prompt = f"""
You are AURA's intelligent planning agent. Current time: {current_time_iso}.
Existing user context: {json.dumps(user_context, default=str)}
Goal prompt from user: "{goal_prompt}"

Parse this goal and return a JSON object adhering exactly to this structure:
{{
  "understood_goal": "string summary",
  "is_ambiguous": false,
  "clarification_question": null,
  "extracted_tasks": [
    {{
      "id": "optional_string",
      "title": "Task title",
      "description": "Task details",
      "estimated_duration_minutes": 30,
      "deadline": "ISO datetime string or null",
      "priority": 3,
      "mandatory": false,
      "dependencies": [],
      "confidence": 0.95
    }}
  ],
  "detected_constraints": ["constraint 1"],
  "explanation": "Rationale"
}}
Return ONLY valid JSON.
"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.endpoint,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean possible markdown wrapping
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            parsed = json.loads(raw_text)
            return StructuredGoalParsingOutput(**parsed)

    async def generate_explanation(
        self,
        scheduled_tasks: list[dict[str, Any]],
        unscheduled_tasks: list[dict[str, Any]],
        conflicts: list[str],
    ) -> str:
        prompt = f"""
Scheduled tasks: {json.dumps(scheduled_tasks, default=str)}
Unscheduled tasks: {json.dumps(unscheduled_tasks, default=str)}
Conflicts: {json.dumps(conflicts)}

Provide a concise, factual explanation for the user explaining the schedule decisions and trade-offs.
"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.endpoint,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    async def suggest_recovery_options(
        self,
        failed_task_title: str,
        error_message: str,
        remaining_tasks: list[dict[str, Any]],
    ) -> str:
        prompt = f"""
Failed task: {failed_task_title}
Error: {error_message}
Remaining tasks: {json.dumps(remaining_tasks, default=str)}

Suggest actionable recovery and replanning recommendations.
"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.endpoint,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
