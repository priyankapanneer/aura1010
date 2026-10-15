import re
from datetime import datetime, timedelta
from typing import Any

from app.integrations.llm.base import LLMProvider
from app.schemas.agent import DecomposedTask, StructuredGoalParsingOutput


class MockLLMProvider(LLMProvider):
    """
    Deterministic, research-grade Mock LLM Provider.
    Clearly labelled as simulated AI inference for testing and offline local development.
    Extracts goals, deadlines, and durations using robust regex & heuristics.
    """

    async def parse_and_decompose_goal(
        self,
        goal_prompt: str,
        current_time_iso: str,
        user_context: dict[str, Any],
    ) -> StructuredGoalParsingOutput:
        prompt_lower = goal_prompt.lower().strip()
        now = datetime.fromisoformat(current_time_iso)

        # Ambiguity check
        if len(prompt_lower.split()) < 3 and ("stuff" in prompt_lower or "plan" == prompt_lower or "help" == prompt_lower):
            return StructuredGoalParsingOutput(
                understood_goal=goal_prompt,
                is_ambiguous=True,
                clarification_question="What specific tasks, deadlines, or priorities would you like me to schedule today?",
                extracted_tasks=[],
                detected_constraints=[],
                explanation="[Simulated AI - Demo Mode] Prompt too brief and underspecified to formulate an action plan.",
            )

        extracted_tasks: list[DecomposedTask] = []
        constraints: list[str] = []

        # Example scenario matching: "Plan my day. I have a project deadline at 5 PM, two meetings, three pending tasks, and I need one hour to study."
        # Or general prompts:
        # Check for 5 PM deadline
        deadline_match = re.search(r"deadline at (\d{1,2})\s*(am|pm)?", prompt_lower)
        five_pm_deadline = None
        if deadline_match:
            hour = int(deadline_match.group(1))
            meridiem = deadline_match.group(2)
            if meridiem == "pm" and hour < 12:
                hour += 12
            five_pm_deadline = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if five_pm_deadline < now:
                five_pm_deadline += timedelta(days=1)
            constraints.append(f"Hard deadline at {five_pm_deadline.strftime('%H:%M')}")

        # Check for study request
        if "study" in prompt_lower or "learn" in prompt_lower:
            duration = 60
            if "half hour" in prompt_lower or "30 min" in prompt_lower:
                duration = 30
            elif "two hour" in prompt_lower or "2 hour" in prompt_lower:
                duration = 120
            extracted_tasks.append(
                DecomposedTask(
                    id="mock_study_01",
                    title="Deep Study / Learning Session",
                    description="Focused uninterrupted study block extracted from goal prompt",
                    estimated_duration_minutes=duration,
                    priority=4,
                    mandatory=True,
                    deadline=five_pm_deadline,
                    dependencies=[],
                    confidence=0.95,
                )
            )

        # Check for urgent/project work
        if "project" in prompt_lower or "urgent" in prompt_lower or "deadline" in prompt_lower:
            extracted_tasks.append(
                DecomposedTask(
                    id="mock_project_01",
                    title="Deliverable: Project Core Milestone",
                    description="High-priority deliverable required before 5 PM deadline",
                    estimated_duration_minutes=90,
                    priority=5,
                    mandatory=True,
                    deadline=five_pm_deadline or (now + timedelta(hours=4)),
                    dependencies=[],
                    confidence=0.98,
                )
            )
            extracted_tasks.append(
                DecomposedTask(
                    id="mock_review_02",
                    title="Code Review & Verification",
                    description="Post-milestone quality check and team signoff",
                    estimated_duration_minutes=30,
                    priority=3,
                    mandatory=False,
                    deadline=five_pm_deadline,
                    dependencies=["mock_project_01"],
                    confidence=0.90,
                )
            )

        # Pending tasks from user context if prompt mentions "pending tasks"
        context_tasks = user_context.get("pending_tasks", [])
        if "pending" in prompt_lower and context_tasks:
            for t in context_tasks[:3]:
                extracted_tasks.append(
                    DecomposedTask(
                        id=t["id"],
                        title=t["title"],
                        description=t.get("description"),
                        estimated_duration_minutes=t.get("estimated_duration_minutes", 30),
                        deadline=datetime.fromisoformat(t["deadline"]) if t.get("deadline") else None,
                        priority=t.get("priority", 3),
                        mandatory=t.get("mandatory", False),
                        dependencies=t.get("dependencies", []),
                        confidence=1.0,
                    )
                )

        # If no specific patterns triggered, generate standard actionable task breakdown from prompt
        if not extracted_tasks:
            extracted_tasks = [
                DecomposedTask(
                    id="mock_task_gen_1",
                    title=f"Execute: {goal_prompt[:40]}",
                    description=f"Action item derived from: '{goal_prompt}'",
                    estimated_duration_minutes=45,
                    priority=4,
                    mandatory=True,
                    deadline=now + timedelta(hours=5),
                    dependencies=[],
                    confidence=0.92,
                ),
                DecomposedTask(
                    id="mock_task_gen_2",
                    title="Review & Verify Results",
                    description="Follow-up validation and testing",
                    estimated_duration_minutes=30,
                    priority=3,
                    mandatory=False,
                    deadline=now + timedelta(hours=6),
                    dependencies=["mock_task_gen_1"],
                    confidence=0.88,
                ),
            ]

        return StructuredGoalParsingOutput(
            understood_goal=goal_prompt,
            is_ambiguous=False,
            clarification_question=None,
            extracted_tasks=extracted_tasks,
            detected_constraints=constraints,
            explanation="[Simulated AI - Demo Mode] Parsed goal into actionable tasks with estimated durations, dependencies, and deadlines.",
        )

    async def generate_explanation(
        self,
        scheduled_tasks: list[dict[str, Any]],
        unscheduled_tasks: list[dict[str, Any]],
        conflicts: list[str],
    ) -> str:
        lines = ["[Simulated AI Decision Explanation]"]
        lines.append(f"Successfully scheduled {len(scheduled_tasks)} tasks within available working windows.")
        if unscheduled_tasks:
            lines.append(f"Could not fit {len(unscheduled_tasks)} low-utility/non-mandatory tasks due to constraint bounds:")
            for ut in unscheduled_tasks:
                lines.append(f" - '{ut.get('task_title', 'Task')}': {ut.get('reason', 'Time limit exceeded')}")
        else:
            lines.append("All high-priority and mandatory work has been cleanly accommodated around fixed calendar events.")
        if conflicts:
            lines.append("Detected conflicts: " + "; ".join(conflicts))
        return "\n".join(lines)

    async def suggest_recovery_options(
        self,
        failed_task_title: str,
        error_message: str,
        remaining_tasks: list[dict[str, Any]],
    ) -> str:
        return (
            f"[Simulated AI Diagnosis] Execution of '{failed_task_title}' encountered: {error_message}. "
            f"Recommended recovery: Defer non-critical dependents, compress buffer windows, or replan remaining "
            f"{len(remaining_tasks)} tasks to preserve the primary deadline."
        )
