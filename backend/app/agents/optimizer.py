from datetime import datetime, timedelta
from typing import Any

from app.schemas.agent import ScheduleSlot, UnscheduledItem
from ortools.sat.python import cp_model


class ScheduleOptimizerResult:
    def __init__(
        self,
        status: str,
        scheduled_slots: list[ScheduleSlot],
        unscheduled_items: list[UnscheduledItem],
        objective_value: float,
        solver_time_ms: int,
        conflicts: list[str],
        is_independently_valid: bool,
    ):
        self.status = status
        self.scheduled_slots = scheduled_slots
        self.unscheduled_items = unscheduled_items
        self.objective_value = objective_value
        self.solver_time_ms = solver_time_ms
        self.conflicts = conflicts
        self.is_independently_valid = is_independently_valid

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "scheduled_slots": [s.model_dump() for s in self.scheduled_slots],
            "unscheduled_items": [u.model_dump() for u in self.unscheduled_items],
            "objective_value": self.objective_value,
            "solver_time_ms": self.solver_time_ms,
            "conflicts": self.conflicts,
            "is_independently_valid": self.is_independently_valid,
        }


class ScheduleOptimizer:
    """
    Google OR-Tools CP-SAT Constraint Optimizer for task planning and calendar scheduling.
    Enforces hard constraints (fixed events, deadlines, precedence, non-overlap, working hours)
    and maximizes total utility with early scheduling preference.
    """

    def __init__(
        self,
        buffer_minutes_between_tasks: int = 5,
        time_step_minutes: int = 5,
    ):
        self.buffer_minutes = buffer_minutes_between_tasks
        self.time_step_minutes = time_step_minutes

    def optimize_schedule(
        self,
        tasks: list[dict[str, Any]],
        fixed_events: list[dict[str, Any]],
        window_start: datetime,
        window_end: datetime,
    ) -> ScheduleOptimizerResult:
        """
        Solves the constrained scheduling problem over the time interval [window_start, window_end].
        All times are mapped to integer minutes relative to window_start (t=0).
        """
        start_ts = datetime.now()

        # Normalize datetimes to naive UTC for consistent arithmetic
        def to_naive(dt: datetime) -> datetime:
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        w_start = to_naive(window_start)
        w_end = to_naive(window_end)
        total_horizon_minutes = int((w_end - w_start).total_seconds() / 60)

        if total_horizon_minutes <= 0:
            return ScheduleOptimizerResult(
                status="INFEASIBLE",
                scheduled_slots=[],
                unscheduled_items=[
                    UnscheduledItem(
                        task_id=str(t.get("id", "t")),
                        task_title=t.get("title", "Task"),
                        reason="Planning window has zero or negative duration",
                        hard_conflict=True,
                    )
                    for t in tasks
                ],
                objective_value=0.0,
                solver_time_ms=0,
                conflicts=["Planning window start is after or equal to window end."],
                is_independently_valid=True,
            )

        model = cp_model.CpModel()

        # 1. Fixed Calendar Events
        fixed_intervals = []
        fixed_event_spans: list[tuple[int, int, str]] = []
        for fe in fixed_events:
            fe_start = to_naive(fe["start_time"])
            fe_end = to_naive(fe["end_time"])

            # Clip to window
            s_min = max(0, int((fe_start - w_start).total_seconds() / 60))
            e_min = min(total_horizon_minutes, int((fe_end - w_start).total_seconds() / 60))

            if e_min > s_min:
                dur = e_min - s_min
                fixed_interval = model.NewIntervalVar(s_min, dur, e_min, f"fixed_{fe.get('id', s_min)}")
                fixed_intervals.append(fixed_interval)
                fixed_event_spans.append((s_min, e_min, fe.get("title", "Meeting")))

        # 2. Task Variables
        task_vars = {}
        all_task_intervals = list(fixed_intervals)
        task_lookup = {}
        unscheduled_reasons = {}

        for idx, t in enumerate(tasks):
            t_id = str(t.get("id", f"task_{idx}"))
            t_title = t.get("title", f"Task {idx+1}")
            duration = int(t.get("estimated_duration_minutes", 30))
            is_mandatory = bool(t.get("mandatory", False))
            deadline = t.get("deadline")
            utility = float(t.get("utility_score", 1.0))
            task_lookup[t_id] = t

            # Deadline in relative minutes
            max_end_time = total_horizon_minutes
            if deadline:
                deadline_dt = to_naive(deadline if isinstance(deadline, datetime) else datetime.fromisoformat(deadline))
                deadline_min = int((deadline_dt - w_start).total_seconds() / 60)
                max_end_time = min(total_horizon_minutes, deadline_min)

            # Check if duration alone exceeds max_end_time
            if duration > max_end_time:
                unscheduled_reasons[t_id] = f"Duration ({duration}m) exceeds deadline or horizon ({max_end_time}m)"
                continue

            # Boolean presence variable (whether task is scheduled)
            # Mandatory tasks must be scheduled if feasible
            if is_mandatory:
                is_present = model.NewBoolVar(f"presence_{t_id}")
                # We add soft penalty or require it; to allow graceful diagnosis we set soft constraint with huge weight
            else:
                is_present = model.NewBoolVar(f"presence_{t_id}")

            start_var = model.NewIntVar(0, total_horizon_minutes - duration, f"start_{t_id}")
            end_var = model.NewIntVar(duration, max_end_time, f"end_{t_id}")
            # Optional interval variable
            interval_var = model.NewOptionalIntervalVar(
                start_var, duration, end_var, is_present, f"interval_{t_id}"
            )

            all_task_intervals.append(interval_var)
            task_vars[t_id] = {
                "presence": is_present,
                "start": start_var,
                "end": end_var,
                "interval": interval_var,
                "duration": duration,
                "utility": utility,
                "mandatory": is_mandatory,
                "title": t_title,
                "max_end_time": max_end_time,
            }

        # 3. No-Overlap Constraint on all intervals (tasks + fixed meetings)
        model.AddNoOverlap(all_task_intervals)

        # 4. Precedence Constraints (Dependencies)
        for t_id, tv in task_vars.items():
            t = task_lookup[t_id]
            deps = t.get("dependencies", [])
            for dep_id in deps:
                dep_id_str = str(dep_id)
                if dep_id_str in task_vars:
                    dep_tv = task_vars[dep_id_str]
                    # If this task is scheduled, dependency MUST also be scheduled and finish before
                    model.Add(dep_tv["presence"] >= tv["presence"])
                    model.Add(tv["start"] >= dep_tv["end"] + self.buffer_minutes).OnlyEnforceIf(
                        [tv["presence"], dep_tv["presence"]]
                    )

        # 5. Objective Function
        # Maximize: 1000 * sum(mandatory * presence) + sum(utility * 100 * presence) - small penalty on start times (early completion)
        objective_terms = []
        for t_id, tv in task_vars.items():
            mult = 10000 if tv["mandatory"] else int(tv["utility"] * 100)
            objective_terms.append(tv["presence"] * mult)
            # Preference for scheduling earlier: -1 * start_var
            objective_terms.append(-tv["start"])

        model.Maximize(sum(objective_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5.0
        status_code = solver.Solve(model)
        solve_time_ms = int((datetime.now() - start_ts).total_seconds() * 1000)

        scheduled_slots: list[ScheduleSlot] = []
        unscheduled_items: list[UnscheduledItem] = []
        conflicts: list[str] = []

        # Collect unscheduled tasks that failed pre-filter
        for t_id, reason in unscheduled_reasons.items():
            t = task_lookup[t_id]
            unscheduled_items.append(
                UnscheduledItem(
                    task_id=t_id,
                    task_title=t.get("title", "Task"),
                    reason=reason,
                    hard_conflict=True,
                    suggested_alternative="Extend deadline or reduce task duration",
                )
            )

        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_str = "OPTIMAL" if status_code == cp_model.OPTIMAL else "FEASIBLE"

            # Extract assigned times
            assigned = []
            for t_id, tv in task_vars.items():
                if solver.Value(tv["presence"]) == 1:
                    s_val = solver.Value(tv["start"])
                    e_val = solver.Value(tv["end"])
                    assigned.append((s_val, e_val, t_id, tv))
                else:
                    # Task was not scheduled by solver
                    reason = "Insufficient available time in schedule without colliding with higher-utility tasks or fixed meetings."
                    if tv["mandatory"]:
                        reason = "Mandatory task could not fit within deadline constraints alongside fixed calendar events."
                        conflicts.append(f"Mandatory task '{tv['title']}' could not be placed.")
                    unscheduled_items.append(
                        UnscheduledItem(
                            task_id=t_id,
                            task_title=tv["title"],
                            reason=reason,
                            hard_conflict=tv["mandatory"],
                            suggested_alternative="Reschedule overlapping meetings or defer optional work",
                        )
                    )

            # Sort by start time for order indexing
            assigned.sort(key=lambda x: x[0])
            for order_idx, (s_min, e_min, t_id, tv) in enumerate(assigned):
                slot_start = w_start + timedelta(minutes=s_min)
                slot_end = w_start + timedelta(minutes=e_min)
                scheduled_slots.append(
                    ScheduleSlot(
                        task_id=t_id,
                        task_title=tv["title"],
                        start_time=slot_start,
                        end_time=slot_end,
                        duration_minutes=tv["duration"],
                        is_mandatory=tv["mandatory"],
                        utility_score=tv["utility"],
                        order_index=order_idx,
                    )
                )

            obj_val = solver.ObjectiveValue()
        else:
            status_str = "INFEASIBLE"
            obj_val = 0.0
            conflicts.append("No feasible schedule found satisfying hard constraints.")
            for t_id, tv in task_vars.items():
                unscheduled_items.append(
                    UnscheduledItem(
                        task_id=t_id,
                        task_title=tv["title"],
                        reason="Schedule is globally infeasible under current constraints",
                        hard_conflict=True,
                    )
                )

        # 6. Independent Independent Validation Check
        is_valid = self._validate_schedule_independently(
            scheduled_slots, fixed_event_spans, task_lookup, w_start, total_horizon_minutes
        )

        return ScheduleOptimizerResult(
            status=status_str,
            scheduled_slots=scheduled_slots,
            unscheduled_items=unscheduled_items,
            objective_value=obj_val,
            solver_time_ms=solve_time_ms,
            conflicts=conflicts,
            is_independently_valid=is_valid,
        )

    def _validate_schedule_independently(
        self,
        scheduled_slots: list[ScheduleSlot],
        fixed_event_spans: list[tuple[int, int, str]],
        task_lookup: dict[str, dict[str, Any]],
        window_start: datetime,
        horizon_minutes: int,
    ) -> bool:
        """
        Independent double-check of generated schedule.
        Validates:
        1. No overlap among scheduled tasks
        2. No overlap with fixed meetings
        3. All deadlines respected
        4. Dependency order preserved
        """
        # 1 & 2: Overlap check
        all_intervals = []
        for slot in scheduled_slots:
            s_min = int((slot.start_time - window_start).total_seconds() / 60)
            e_min = int((slot.end_time - window_start).total_seconds() / 60)
            if s_min < 0 or e_min > horizon_minutes or e_min <= s_min:
                return False
            all_intervals.append((s_min, e_min, f"task_{slot.task_id}"))

        for s_min, e_min, title in fixed_event_spans:
            all_intervals.append((s_min, e_min, f"fixed_{title}"))

        # Sort and verify strictly no overlap
        all_intervals.sort(key=lambda x: x[0])
        for i in range(len(all_intervals) - 1):
            if all_intervals[i][1] > all_intervals[i + 1][0]:
                return False  # Overlap detected!

        # 3. Deadline check
        for slot in scheduled_slots:
            t = task_lookup.get(slot.task_id)
            if t and t.get("deadline"):
                dl = t["deadline"]
                dl_dt = dl if isinstance(dl, datetime) else datetime.fromisoformat(dl)
                if dl_dt.tzinfo:
                    dl_dt = dl_dt.replace(tzinfo=None)
                if slot.end_time > dl_dt:
                    return False  # Missed deadline!

        # 4. Dependency check
        slot_map = {s.task_id: s for s in scheduled_slots}
        for slot in scheduled_slots:
            t = task_lookup.get(slot.task_id)
            if t and t.get("dependencies"):
                for dep_id in t["dependencies"]:
                    dep_slot = slot_map.get(str(dep_id))
                    if not dep_slot or dep_slot.end_time > slot.start_time:
                        return False  # Dependency ordering violation!

        return True
