from datetime import datetime, timedelta

from app.agents.optimizer import ScheduleOptimizer


def test_optimizer_avoids_fixed_events_and_respects_dependencies():
    optimizer = ScheduleOptimizer(buffer_minutes_between_tasks=5)
    now = datetime(2026, 10, 13, 9, 0, 0)
    horizon_end = now + timedelta(hours=8)  # 09:00 to 17:00

    # Fixed meeting from 11:00 to 12:00
    fixed_events = [
        {
            "id": "meeting_1",
            "title": "Team Sync",
            "start_time": now + timedelta(hours=2),
            "end_time": now + timedelta(hours=3),
        }
    ]

    # Task 1 (60 min), Task 2 depends on Task 1 (60 min)
    tasks = [
        {
            "id": "t1",
            "title": "Data Ingestion",
            "estimated_duration_minutes": 60,
            "mandatory": True,
            "utility_score": 1.5,
            "dependencies": [],
            "deadline": horizon_end,
        },
        {
            "id": "t2",
            "title": "Model Training",
            "estimated_duration_minutes": 60,
            "mandatory": True,
            "utility_score": 1.4,
            "dependencies": ["t1"],
            "deadline": horizon_end,
        },
    ]

    result = optimizer.optimize_schedule(tasks, fixed_events, now, horizon_end)

    assert result.status in ("OPTIMAL", "FEASIBLE")
    assert result.is_independently_valid is True
    assert len(result.scheduled_slots) == 2

    # Check dependency: t2 must start after t1 ends
    slot_map = {s.task_id: s for s in result.scheduled_slots}
    assert slot_map["t2"].start_time >= slot_map["t1"].end_time + timedelta(minutes=5)

    # Check that neither task collides with 11:00 - 12:00 meeting
    meeting_start = now + timedelta(hours=2)
    meeting_end = now + timedelta(hours=3)
    for slot in result.scheduled_slots:
        assert not (slot.start_time < meeting_end and slot.end_time > meeting_start)


def test_optimizer_handles_overbooked_schedule_gracefully():
    optimizer = ScheduleOptimizer(buffer_minutes_between_tasks=5)
    now = datetime(2026, 10, 13, 9, 0, 0)
    horizon_end = now + timedelta(hours=3)  # 3 hours = 180 min total

    # 4 tasks of 60 min each (240 min needed > 180 min available)
    tasks = [
        {
            "id": "mand_task",
            "title": "Critical Client Fix",
            "estimated_duration_minutes": 60,
            "mandatory": True,
            "utility_score": 2.0,
        },
        {
            "id": "opt_task_1",
            "title": "Documentation",
            "estimated_duration_minutes": 60,
            "mandatory": False,
            "utility_score": 0.8,
        },
        {
            "id": "opt_task_2",
            "title": "Refactoring",
            "estimated_duration_minutes": 60,
            "mandatory": False,
            "utility_score": 0.5,
        },
        {
            "id": "opt_task_3",
            "title": "Inbox Zero",
            "estimated_duration_minutes": 60,
            "mandatory": False,
            "utility_score": 0.3,
        },
    ]

    result = optimizer.optimize_schedule(tasks, [], now, horizon_end)

    assert result.status in ("OPTIMAL", "FEASIBLE")
    assert result.is_independently_valid is True

    # Mandatory task MUST be scheduled
    scheduled_ids = [s.task_id for s in result.scheduled_slots]
    assert "mand_task" in scheduled_ids

    # Unscheduled items must explain why
    assert len(result.unscheduled_items) >= 1
    assert any("Insufficient" in u.reason for u in result.unscheduled_items)
