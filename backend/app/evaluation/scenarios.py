from datetime import datetime, timedelta
from typing import Any


def get_evaluation_scenarios(base_time: datetime) -> list[dict[str, Any]]:
    horizon_start = base_time.replace(hour=9, minute=0, second=0, microsecond=0)
    horizon_end = base_time.replace(hour=17, minute=0, second=0, microsecond=0)

    return [
        {
            "name": "Scenario 1: Conflicting Deadlines & Overbooked Window",
            "description": "8 candidate tasks totaling 9.5 hours within an 8-hour day with a 1-hour fixed meeting.",
            "window_start": horizon_start,
            "window_end": horizon_end,
            "fixed_events": [
                {
                    "id": "fe_sync",
                    "title": "All-Hands Sync",
                    "start_time": horizon_start + timedelta(hours=2),
                    "end_time": horizon_start + timedelta(hours=3),
                }
            ],
            "tasks": [
                {
                    "id": "t1",
                    "title": "Client Deliverable Alpha",
                    "estimated_duration_minutes": 120,
                    "deadline": horizon_start + timedelta(hours=4),
                    "priority": 5,
                    "mandatory": True,
                    "dependencies": [],
                },
                {
                    "id": "t2",
                    "title": "Security Hotfix",
                    "estimated_duration_minutes": 60,
                    "deadline": horizon_start + timedelta(hours=5),
                    "priority": 5,
                    "mandatory": True,
                    "dependencies": [],
                },
                {
                    "id": "t3",
                    "title": "Feature Refactoring",
                    "estimated_duration_minutes": 90,
                    "deadline": horizon_end,
                    "priority": 3,
                    "mandatory": False,
                    "dependencies": ["t1"],
                },
                {
                    "id": "t4",
                    "title": "Write API Docs",
                    "estimated_duration_minutes": 60,
                    "deadline": horizon_end,
                    "priority": 2,
                    "mandatory": False,
                    "dependencies": [],
                },
                {
                    "id": "t5",
                    "title": "Database Optimization",
                    "estimated_duration_minutes": 90,
                    "deadline": horizon_end,
                    "priority": 4,
                    "mandatory": False,
                    "dependencies": [],
                },
                {
                    "id": "t6",
                    "title": "Team 1-on-1 Prep",
                    "estimated_duration_minutes": 30,
                    "deadline": horizon_start + timedelta(hours=3),
                    "priority": 3,
                    "mandatory": False,
                    "dependencies": [],
                },
                {
                    "id": "t7",
                    "title": "Research Paper Review",
                    "estimated_duration_minutes": 60,
                    "deadline": horizon_end,
                    "priority": 1,
                    "mandatory": False,
                    "dependencies": [],
                },
                {
                    "id": "t8",
                    "title": "Log Triage",
                    "estimated_duration_minutes": 60,
                    "deadline": horizon_end,
                    "priority": 2,
                    "mandatory": False,
                    "dependencies": [],
                },
            ],
        },
        {
            "name": "Scenario 2: Deep Cascading Dependencies",
            "description": "Chain of 4 sequential dependencies with narrow interleaving free blocks.",
            "window_start": horizon_start,
            "window_end": horizon_end,
            "fixed_events": [
                {
                    "id": "fe_standup",
                    "title": "Daily Standup",
                    "start_time": horizon_start + timedelta(minutes=30),
                    "end_time": horizon_start + timedelta(minutes=60),
                },
                {
                    "id": "fe_lunch",
                    "title": "Lunch Break",
                    "start_time": horizon_start + timedelta(hours=3, minutes=30),
                    "end_time": horizon_start + timedelta(hours=4, minutes=30),
                },
            ],
            "tasks": [
                {
                    "id": "dep_1",
                    "title": "Data Pipeline Setup",
                    "estimated_duration_minutes": 60,
                    "priority": 4,
                    "mandatory": True,
                    "dependencies": [],
                },
                {
                    "id": "dep_2",
                    "title": "ETL Feature Extraction",
                    "estimated_duration_minutes": 60,
                    "priority": 4,
                    "mandatory": True,
                    "dependencies": ["dep_1"],
                },
                {
                    "id": "dep_3",
                    "title": "Model Training Run",
                    "estimated_duration_minutes": 90,
                    "priority": 5,
                    "mandatory": True,
                    "dependencies": ["dep_2"],
                },
                {
                    "id": "dep_4",
                    "title": "Validation & Metrics Reporting",
                    "estimated_duration_minutes": 45,
                    "priority": 4,
                    "mandatory": True,
                    "dependencies": ["dep_3"],
                },
            ],
        },
        {
            "name": "Scenario 3: Dynamic Task Slippage & Urgent Task Insertion",
            "description": "Initial task runs over duration by 100%, triggering adaptive replanning to fit a newly inserted critical task.",
            "window_start": horizon_start,
            "window_end": horizon_end,
            "fixed_events": [],
            "tasks": [
                {
                    "id": "slip_1",
                    "title": "Unexpected Production Outage",
                    "estimated_duration_minutes": 90,
                    "priority": 5,
                    "mandatory": True,
                    "dependencies": [],
                    "deadline": horizon_start + timedelta(hours=3),
                },
                {
                    "id": "slip_2",
                    "title": "Followup Post-Mortem",
                    "estimated_duration_minutes": 60,
                    "priority": 4,
                    "mandatory": True,
                    "dependencies": ["slip_1"],
                },
                {
                    "id": "slip_3",
                    "title": "Normal Backlog Work",
                    "estimated_duration_minutes": 120,
                    "priority": 2,
                    "mandatory": False,
                    "dependencies": [],
                },
            ],
        },
    ]
