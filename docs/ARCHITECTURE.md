# AURA Architecture Specification

## 1. Executive Summary

**AURA** (Adaptive Utility-Aware AI Assistant for Real-Time Task Planning and Execution) is a hybrid cognitive-operational system. It pairs Large Language Models for unstructured intent parsing, task decomposition, and semantic reasoning with deterministic Operations Research constraint programming (Google OR-Tools CP-SAT) for provably feasible, collision-free time allocation.

Unlike traditional static assistants or chat-only interfaces, AURA provides:
1. **Utility-Driven Prioritization**: Tasks are prioritized by urgency, user importance, goal impact, dependency depth, and duration efficiency.
2. **Deterministic Schedule Feasibility**: Schedules obey hard constraints (fixed events, deadlines, dependency ordering, non-overlap) using Google OR-Tools.
3. **Stateful Graph Execution with Human-in-the-Loop**: Built on LangGraph, workflows interrupt before external or consequential operations and resume reliably upon approval.
4. **Adaptive Closed-Loop Replanning**: Dynamic adjustments occur when tasks slip, new events arrive, tool operations fail, or constraints are updated.
5. **Verified Tool Execution**: Actions are audited and validated server-side. No action is reported as successful without provider confirmation.

---

## 2. Layered System Architecture

```
+-------------------------------------------------------------------------+
|                        PRESENTATION LAYER (React)                       |
|  - Dashboard: Status summary, current timeline, priority queue          |
|  - AI Planner: Natural-language input, schedule inspection, approval UI |
|  - Calendar: Visual day/week view with fixed vs. planned task separation|
|  - Task Manager: Filterable, sortable CRUD with dependency graph editor |
|  - Plan History: Plan diff viewer and audit log                         |
|  - Settings: Working hours, utility weights, LLM configuration status    |
+------------------------------------+------------------------------------+
                                     | Typed REST & SSE
+------------------------------------v------------------------------------+
|                         APPLICATION LAYER (FastAPI)                     |
|  - /api/v1/tasks, /plans, /calendar, /settings, /history, /eval         |
|  - Authentication & Tenant Isolation (multi-user ready)                 |
|  - Service Layer & Repository Pattern (Clean Architecture)              |
+------------------+----------------------------------+-------------------+
                   |                                  |
+------------------v---------------+  +---------------v-------------------+
|      ORCHESTRATION & REASONING   |  |     DETERMINISTIC OPTIMIZATION    |
|  - LangGraph State Machine       |  |  - Google OR-Tools CP-SAT Solver   |
|  - LLM Provider Abstraction      |  |  - Hard constraint enforcement    |
|  - Structured Pydantic Output    |  |  - Multi-objective utility max    |
|  - HITL Approval Checkpointing   |  |  - Unscheduled conflict detection |
+------------------+---------------+  +---------------+-------------------+
                   |                                  |
+------------------v----------------------------------v-------------------+
|                           PERSISTENCE LAYER                             |
|  - PostgreSQL 16 (Primary) / SQLite (Standalone dev fallback)           |
|  - SQLAlchemy 2.0 ORM + Alembic versioned migrations                    |
|  - Tables: users, tasks, dependencies, events, plans, audits, checks   |
+-------------------------------------------------------------------------+
```

---

## 3. Core Subsystems

### 3.1 LLM Provider Abstraction
The system isolates the AI model behind a generic `LLMProvider` interface (`backend/app/integrations/llm/base.py`):
- `MockLLMProvider`: Deterministic, high-fidelity mock supporting local offline execution, automated testing, and CI/CD without API costs.
- `GeminiProvider`: Google Gemini 2.5 Flash / Pro API integration.
- `OpenAIProvider`: OpenAI GPT-4o / GPT-4o-mini API integration.
- `AnthropicProvider`: Claude 3.5 Sonnet API integration.

### 3.2 Constraint Optimization Engine (OR-Tools CP-SAT)
Rather than trusting language models with temporal arithmetic (where hallucinated time overlaps and missed deadlines are endemic), AURA translates the task portfolio and calendar state into a Constraint Programming problem:
- **Interval Variables**: For each candidate task $i$, $s_i \in [T_{\text{start}}, T_{\text{end}}]$, duration $d_i$, end $e_i = s_i + d_i$.
- **No-Overlap Constraint**: `AddNoOverlap(all_intervals + fixed_calendar_intervals)`.
- **Precedence Constraint**: For task $B$ depending on $A$, $e_A \le s_B$.
- **Deadline Constraint**: $e_i \le \text{deadline}_i$. If infeasible, task marked unscheduled with conflict diagnostic.
- **Objective Function**: Maximize $\sum (U_i \cdot \text{scheduled}_i) - \text{penalty} \cdot \text{tardiness}$.

### 3.3 Human-in-the-Loop & LangGraph Checkpointing
All proposed plans requiring external calendar sync or database commitments trigger an interrupt node.
- The plan status transitions to `PROPOSED`.
- The user can review the schedule diff, priority explanations, and unscheduled trade-offs.
- Upon explicit `approve`, the graph resumes at `execute_approved_actions`.
- Upon `reject`, the graph routes to `handle_rejection` without side effects.
