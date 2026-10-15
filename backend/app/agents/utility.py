import math
from datetime import datetime
from typing import Any

from app.schemas.agent import UtilityBreakdown


class UtilityCalculator:
    """
    Explicit, documented multi-factor utility scoring engine.

    Formula:
    Utility(i) = w_urgency * U_urgency(i)
               + w_importance * U_importance(i)
               + w_impact * U_impact(i)
               + w_dependency * U_dependency(i)
               + w_efficiency * U_efficiency(i)
               + B_mandatory(i)

    Weights:
    Configurable via user settings, defaulting to:
      - w_urgency: 0.35
      - w_importance: 0.25
      - w_impact: 0.15
      - w_dependency: 0.15
      - w_efficiency: 0.10
    Total weights sum to 1.0.

    Component Definitions:
    1. U_urgency(i):
       Slack = (Deadline - CurrentTime) - Duration.
       If Slack <= 0: urgency = 1.0 (Critical / At or past deadline).
       Otherwise, urgency = max(0.0, 1.0 - (Slack / PlanningHorizon)).
       PlanningHorizon defaults to 480 minutes (8 working hours).

    2. U_importance(i):
       Normalized from user priority P in [1..5]: (P - 1) / 4.0.

    3. U_impact(i):
       Direct impact score in [0.0, 1.0] or inferred from confidence * normalized priority.

    4. U_dependency(i):
       Centrality = (Number of downstream dependent tasks) / max(1, Total tasks - 1).
       Tasks blocking others receive higher utility to prevent bottlenecks.

    5. U_efficiency(i):
       Duration penalty/yield curve: prefer high-utility manageable blocks.
       U_efficiency = 1.0 / (1.0 + ln(1.0 + duration / 30.0)).

    6. B_mandatory(i):
       Mandatory tasks receive a 1.0 bonus ensuring priority in competitive selection,
       while hard deadline constraints remain non-negotiable.
    """

    def __init__(self, weights: dict[str, float] | None = None, planning_horizon_minutes: int = 480):
        self.weights = weights or {
            "urgency": 0.35,
            "importance": 0.25,
            "impact": 0.15,
            "dependency": 0.15,
            "efficiency": 0.10,
        }
        self.planning_horizon_minutes = planning_horizon_minutes

    def calculate_task_utility(
        self,
        task: dict[str, Any],
        current_time: datetime,
        dependency_graph: dict[str, list[str]] | None = None,
        total_tasks_count: int = 1,
    ) -> UtilityBreakdown:
        task_id = str(task.get("id", "task"))
        duration = int(task.get("estimated_duration_minutes", 30))
        deadline = task.get("deadline")
        priority = int(task.get("priority", 3))
        mandatory = bool(task.get("mandatory", False))
        confidence = float(task.get("confidence", 1.0))

        # 1. Urgency Score
        urgency_score = 0.2  # Default baseline when no deadline specified
        if deadline:
            if isinstance(deadline, str):
                deadline_dt = datetime.fromisoformat(deadline)
            else:
                deadline_dt = deadline

            # Normalize timezones if needed
            if deadline_dt.tzinfo is not None and current_time.tzinfo is None:
                deadline_dt = deadline_dt.replace(tzinfo=None)
            elif deadline_dt.tzinfo is None and current_time.tzinfo is not None:
                current_time = current_time.replace(tzinfo=None)

            diff_minutes = (deadline_dt - current_time).total_seconds() / 60.0
            slack_minutes = diff_minutes - duration

            if slack_minutes <= 0:
                urgency_score = 1.0
            else:
                urgency_score = max(0.0, min(1.0, 1.0 - (slack_minutes / self.planning_horizon_minutes)))

        # 2. Importance Score: Map 1..5 to 0.0..1.0
        priority_clamped = max(1, min(5, priority))
        importance_score = (priority_clamped - 1) / 4.0

        # 3. Impact Score
        impact_score = min(1.0, max(0.0, importance_score * confidence))

        # 4. Dependency Centrality Score
        # Count how many other tasks depend on this task
        dependents_count = 0
        if dependency_graph:
            # dependency_graph maps task_id -> list of tasks that task_id depends on
            # We want tasks that depend ON this task:
            for other_id, prereqs in dependency_graph.items():
                if task_id in prereqs:
                    dependents_count += 1

        denom = max(1, total_tasks_count - 1)
        dependency_score = min(1.0, dependents_count / denom)

        # 5. Efficiency Score: 1 / (1 + ln(1 + duration/30))
        efficiency_score = 1.0 / (1.0 + math.log(1.0 + max(5, duration) / 30.0))

        # 6. Mandatory Bonus
        mandatory_bonus = 1.0 if mandatory else 0.0

        # Weighted Total
        w_urg = self.weights.get("urgency", 0.35)
        w_imp = self.weights.get("importance", 0.25)
        w_impact = self.weights.get("impact", 0.15)
        w_dep = self.weights.get("dependency", 0.15)
        w_eff = self.weights.get("efficiency", 0.10)

        weighted_base = (
            w_urg * urgency_score
            + w_imp * importance_score
            + w_impact * impact_score
            + w_dep * dependency_score
            + w_eff * efficiency_score
        )
        total_utility = round(weighted_base + mandatory_bonus, 4)

        explanation = (
            f"Utility {total_utility:.2f}: Urgency={urgency_score:.2f} (w={w_urg}), "
            f"Importance={importance_score:.2f} (w={w_imp}), "
            f"Impact={impact_score:.2f} (w={w_impact}), "
            f"DepCentrality={dependency_score:.2f} (w={w_dep}, blocks={dependents_count}), "
            f"Efficiency={efficiency_score:.2f} (w={w_eff})"
            + (" + Mandatory Bonus(+1.0)" if mandatory else "")
        )

        return UtilityBreakdown(
            task_id=task_id,
            urgency_score=round(urgency_score, 3),
            importance_score=round(importance_score, 3),
            impact_score=round(impact_score, 3),
            dependency_score=round(dependency_score, 3),
            efficiency_score=round(efficiency_score, 3),
            mandatory_bonus=round(mandatory_bonus, 2),
            total_utility=total_utility,
            explanation=explanation,
        )
