from abc import ABC, abstractmethod
from typing import Any

from app.schemas.agent import StructuredGoalParsingOutput


class LLMProvider(ABC):
    @abstractmethod
    async def parse_and_decompose_goal(
        self,
        goal_prompt: str,
        current_time_iso: str,
        user_context: dict[str, Any],
    ) -> StructuredGoalParsingOutput:
        """Parses natural-language user goal and decomposes it into structured tasks."""

    @abstractmethod
    async def generate_explanation(
        self,
        scheduled_tasks: list[dict[str, Any]],
        unscheduled_tasks: list[dict[str, Any]],
        conflicts: list[str],
    ) -> str:
        """Generates clear, concise human-facing explanation of why tasks were scheduled or dropped."""

    @abstractmethod
    async def suggest_recovery_options(
        self,
        failed_task_title: str,
        error_message: str,
        remaining_tasks: list[dict[str, Any]],
    ) -> str:
        """Generates diagnosis and recovery strategy when a task or tool action fails."""
