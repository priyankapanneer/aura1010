from datetime import datetime, timedelta

from app.agents.utility import UtilityCalculator


def test_utility_calculator_deadline_urgency():
    calc = UtilityCalculator(planning_horizon_minutes=480)
    now = datetime(2026, 10, 13, 9, 0, 0)

    # Task A: 60 min duration, deadline in 60 min (Slack = 0 -> Urgency = 1.0)
    task_a = {
        "id": "task_a",
        "title": "Urgent Deliverable",
        "estimated_duration_minutes": 60,
        "deadline": now + timedelta(minutes=60),
        "priority": 3,
        "mandatory": False,
        "confidence": 1.0,
    }

    # Task B: 60 min duration, deadline in 480 min (Slack = 420 -> Low Urgency)
    task_b = {
        "id": "task_b",
        "title": "Relaxed Task",
        "estimated_duration_minutes": 60,
        "deadline": now + timedelta(minutes=480),
        "priority": 3,
        "mandatory": False,
        "confidence": 1.0,
    }

    res_a = calc.calculate_task_utility(task_a, now)
    res_b = calc.calculate_task_utility(task_b, now)

    assert res_a.urgency_score == 1.0
    assert res_b.urgency_score < res_a.urgency_score
    assert res_a.total_utility > res_b.total_utility


def test_utility_calculator_mandatory_bonus():
    calc = UtilityCalculator()
    now = datetime(2026, 10, 13, 9, 0, 0)

    task_optional = {
        "id": "opt_1",
        "title": "Optional Task",
        "estimated_duration_minutes": 30,
        "priority": 3,
        "mandatory": False,
    }
    task_mandatory = {
        "id": "mand_1",
        "title": "Mandatory Task",
        "estimated_duration_minutes": 30,
        "priority": 3,
        "mandatory": True,
    }

    res_opt = calc.calculate_task_utility(task_optional, now)
    res_mand = calc.calculate_task_utility(task_mandatory, now)

    assert res_mand.mandatory_bonus == 1.0
    assert res_opt.mandatory_bonus == 0.0
    assert res_mand.total_utility >= res_opt.total_utility + 0.99


def test_utility_dependency_centrality():
    calc = UtilityCalculator()
    now = datetime(2026, 10, 13, 9, 0, 0)

    task_parent = {"id": "task_parent", "estimated_duration_minutes": 30, "priority": 3}
    task_child = {"id": "task_child", "estimated_duration_minutes": 30, "priority": 3}

    # task_child depends on task_parent
    dep_graph = {"task_child": ["task_parent"]}

    res_parent = calc.calculate_task_utility(task_parent, now, dependency_graph=dep_graph, total_tasks_count=2)
    res_child = calc.calculate_task_utility(task_child, now, dependency_graph=dep_graph, total_tasks_count=2)

    assert res_parent.dependency_score == 1.0
    assert res_child.dependency_score == 0.0
    assert res_parent.total_utility > res_child.total_utility
