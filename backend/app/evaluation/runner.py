import time
from datetime import UTC, datetime, timedelta
from typing import Any

from app.agents.optimizer import ScheduleOptimizer
from app.agents.utility import UtilityCalculator
from app.evaluation.scenarios import get_evaluation_scenarios


class EvaluationRunner:
    """
    Empirical Evaluation Benchmark Runner.
    Executes reproducible comparison between:
      Method A: Static LLM (Naive sequential heuristic without constraint optimization)
      Method B: Standard OR-Tools (Constraint scheduler with unweighted / FIFO priority)
      Method C: AURA Full System (Utility-Aware CP-SAT with Adaptive Replanning)
    """

    def __init__(self):
        self.optimizer = ScheduleOptimizer(buffer_minutes_between_tasks=5)
        self.utility_calc = UtilityCalculator()

    def run_benchmark(self) -> dict[str, Any]:
        base_time = datetime(2026, 10, 13, 9, 0, 0)
        scenarios = get_evaluation_scenarios(base_time)

        results_by_method = {
            "Method A (Static LLM / Heuristic)": {
                "feasible_schedules": 0,
                "total_violations": 0,
                "total_utility_achieved": 0.0,
                "scheduled_tasks_count": 0,
                "total_tasks_count": 0,
                "avg_latency_ms": 0.0,
            },
            "Method B (Unweighted Constraint Scheduler)": {
                "feasible_schedules": 0,
                "total_violations": 0,
                "total_utility_achieved": 0.0,
                "scheduled_tasks_count": 0,
                "total_tasks_count": 0,
                "avg_latency_ms": 0.0,
            },
            "Method C (AURA Hybrid Utility-Aware)": {
                "feasible_schedules": 0,
                "total_violations": 0,
                "total_utility_achieved": 0.0,
                "scheduled_tasks_count": 0,
                "total_tasks_count": 0,
                "avg_latency_ms": 0.0,
            },
        }

        scenario_details = []

        for sc in scenarios:
            tasks = sc["tasks"]
            fixed_events = sc["fixed_events"]
            w_start = sc["window_start"]
            w_end = sc["window_end"]

            total_tasks = len(tasks)

            # --- Method A: Static Sequential Heuristic ---
            t0 = time.time()
            method_a_scheduled = []
            method_a_violations = 0
            curr_cursor = w_start
            method_a_utility = 0.0

            for t in tasks:
                dur = t["estimated_duration_minutes"]
                s_time = curr_cursor
                e_time = curr_cursor + timedelta(minutes=dur)
                curr_cursor = e_time

                # Check if e_time collides with fixed events
                collides = any(
                    (s_time < fe["end_time"] and e_time > fe["start_time"]) for fe in fixed_events
                )
                deadline_violation = bool(t.get("deadline") and e_time > t["deadline"])
                horizon_violation = e_time > w_end

                if collides or deadline_violation or horizon_violation:
                    method_a_violations += 1

                method_a_scheduled.append(t["id"])
                # Compute utility for comparison
                u_res = self.utility_calc.calculate_task_utility(t, w_start)
                method_a_utility += u_res.total_utility

            lat_a = (time.time() - t0) * 1000

            # --- Method B: Standard OR-Tools without Utility (equal/FIFO weight) ---
            t0 = time.time()
            tasks_unweighted = [dict(t, utility_score=1.0) for t in tasks]
            res_b = self.optimizer.optimize_schedule(tasks_unweighted, fixed_events, w_start, w_end)
            lat_b = (time.time() - t0) * 1000

            util_b = 0.0
            for slot in res_b.scheduled_slots:
                orig_t = next(t for t in tasks if t["id"] == slot.task_id)
                u_res = self.utility_calc.calculate_task_utility(orig_t, w_start)
                util_b += u_res.total_utility

            # --- Method C: AURA Hybrid System (Utility-weighted CP-SAT) ---
            t0 = time.time()
            tasks_weighted = []
            for t in tasks:
                u_res = self.utility_calc.calculate_task_utility(t, w_start)
                tasks_weighted.append(dict(t, utility_score=u_res.total_utility))

            res_c = self.optimizer.optimize_schedule(tasks_weighted, fixed_events, w_start, w_end)
            lat_c = (time.time() - t0) * 1000

            util_c = sum(slot.utility_score for slot in res_c.scheduled_slots)

            # Record metrics
            results_by_method["Method A (Static LLM / Heuristic)"]["total_violations"] += method_a_violations
            results_by_method["Method A (Static LLM / Heuristic)"]["total_utility_achieved"] += method_a_utility
            results_by_method["Method A (Static LLM / Heuristic)"]["scheduled_tasks_count"] += len(method_a_scheduled)
            results_by_method["Method A (Static LLM / Heuristic)"]["total_tasks_count"] += total_tasks
            results_by_method["Method A (Static LLM / Heuristic)"]["avg_latency_ms"] += lat_a
            if method_a_violations == 0:
                results_by_method["Method A (Static LLM / Heuristic)"]["feasible_schedules"] += 1

            results_by_method["Method B (Unweighted Constraint Scheduler)"]["total_utility_achieved"] += util_b
            results_by_method["Method B (Unweighted Constraint Scheduler)"]["scheduled_tasks_count"] += len(res_b.scheduled_slots)
            results_by_method["Method B (Unweighted Constraint Scheduler)"]["total_tasks_count"] += total_tasks
            results_by_method["Method B (Unweighted Constraint Scheduler)"]["avg_latency_ms"] += lat_b
            if res_b.is_independently_valid and res_b.status in ("OPTIMAL", "FEASIBLE"):
                results_by_method["Method B (Unweighted Constraint Scheduler)"]["feasible_schedules"] += 1

            results_by_method["Method C (AURA Hybrid Utility-Aware)"]["total_utility_achieved"] += util_c
            results_by_method["Method C (AURA Hybrid Utility-Aware)"]["scheduled_tasks_count"] += len(res_c.scheduled_slots)
            results_by_method["Method C (AURA Hybrid Utility-Aware)"]["total_tasks_count"] += total_tasks
            results_by_method["Method C (AURA Hybrid Utility-Aware)"]["avg_latency_ms"] += lat_c
            if res_c.is_independently_valid and res_c.status in ("OPTIMAL", "FEASIBLE"):
                results_by_method["Method C (AURA Hybrid Utility-Aware)"]["feasible_schedules"] += 1

            scenario_details.append({
                "scenario_name": sc["name"],
                "total_tasks": total_tasks,
                "method_a": {
                    "violations": method_a_violations,
                    "scheduled": len(method_a_scheduled),
                    "utility": round(method_a_utility, 2),
                },
                "method_b": {
                    "violations": len(res_b.conflicts),
                    "scheduled": len(res_b.scheduled_slots),
                    "utility": round(util_b, 2),
                },
                "method_c": {
                    "violations": len(res_c.conflicts),
                    "scheduled": len(res_c.scheduled_slots),
                    "utility": round(util_c, 2),
                },
            })

        total_scenarios = len(scenarios)
        summary = {}
        for m_name, m_data in results_by_method.items():
            summary[m_name] = {
                "feasibility_rate_pct": round((m_data["feasible_schedules"] / total_scenarios) * 100, 1),
                "hard_constraint_violations": m_data["total_violations"],
                "total_utility_achieved": round(m_data["total_utility_achieved"], 2),
                "scheduled_task_completion_pct": round((m_data["scheduled_tasks_count"] / m_data["total_tasks_count"]) * 100, 1),
                "avg_latency_ms": round(m_data["avg_latency_ms"] / total_scenarios, 2),
            }

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "scenarios_evaluated": total_scenarios,
            "method_summary": summary,
            "scenario_details": scenario_details,
        }
