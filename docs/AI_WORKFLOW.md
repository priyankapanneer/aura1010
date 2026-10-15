# AURA AI & Agent Workflow Specification

## 1. LangGraph State Machine Architecture

The AURA orchestration layer is implemented as a stateful computational graph using LangGraph. State is preserved across turns via checkpointer storage.

```
       [START]
          │
          ▼
     parse_goal  ────────(Ambiguous intent)───────► ask_clarification ──► [PAUSE / INPUT]
          │                                                                      │
          │ (Clear intent)                                                       │
          ▼                                                                      │
   load_user_context ◄───────────────────────────────────────────────────────────┘
          │
          ▼
   decompose_tasks
          │
          ▼
   calculate_utility
          │
          ▼
   generate_schedule (OR-Tools CP-SAT)
          │
          ▼
   validate_constraints
     /            \
(Violations)      (Valid)
   /                \
revise_schedule       \
   \                /
    ▼              ▼
      present_plan
          │
          ▼
   request_approval ─────► [INTERRUPT: Human Approval Required]
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
               [APPROVED]              [REJECTED]
                    │                       │
                    ▼                       ▼
       execute_approved_actions     handle_rejection ──► [END]
                    │
                    ▼
            verify_execution
             /             \
       (Verified)        (Failed)
           /                 \
          ▼                   ▼
    update_memory      trigger_replanning ──► [Loop to calculate_utility]
          │
          ▼
        [END]
```

---

## 2. Graph State Schema

The persistent graph state dictionary (`AuraState`) includes:
- `user_id`: Identifier for the acting tenant.
- `goal_prompt`: The natural language request from the user.
- `extracted_tasks`: List of decomposed tasks with estimated durations, deadlines, and dependencies.
- `user_context`: Current calendar fixtures, pending tasks, work hours, and utility weights.
- `utility_scores`: Per-task utility breakdown and explanatory metadata.
- `scheduled_items`: Output of the OR-Tools optimizer (start time, end time, status).
- `unscheduled_items`: Tasks that could not fit, paired with constraint conflict explanations.
- `approval_status`: `'PENDING'`, `'APPROVED'`, or `'REJECTED'`.
- `execution_results`: Logs of executed calendar/task actions with verification hashes.
- `replanning_trigger`: Optional reason if execution or context changes forced replanning.
- `clarification_prompt`: Question to the user if intent was underspecified.

---

## 3. Human-in-the-Loop Approval Contract

1. **Autonomous Read**: The agent may inspect existing calendar events and pending tasks without prior approval.
2. **Consequential Write Gate**: Any action that creates, updates, or deletes calendar events, or modifies external services, halts graph execution via `interrupt`.
3. **Audit Trail**: Every approval, rejection, and subsequent execution outcome is recorded in `approval_requests` and `tool_execution_logs`.
4. **Idempotency**: Approved tool executions pass an idempotency key ($UUID$) to prevent duplicate writes during network reconnects or retry loops.
