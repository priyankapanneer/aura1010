# AURA: Adaptive Utility-Aware AI Assistant for Real-Time Task Planning and Execution

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_AI-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![Google OR-Tools](https://img.shields.io/badge/Google_OR--Tools-CP--SAT-4285F4.svg)](https://developers.google.com/optimization)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org)

---

## 1. Executive Summary & Product Vision

**AURA** is an intelligent task-planning and execution platform designed to resolve the limitations of traditional chatbots and static task managers. By coupling the generative reasoning of Large Language Models with the deterministic optimization of **Google OR-Tools CP-SAT** and the stateful orchestration of **LangGraph**, AURA transforms unstructured goals into mathematically optimized, collision-free schedules.

AURA provides:
1. **Semantic Intent & Task Decomposition**: Extracts tasks, durations, deadlines, and dependencies from natural language.
2. **Normalized Multi-Factor Utility Scoring**: Transparently weights urgency, user importance, goal impact, dependency depth, and duration efficiency.
3. **Deterministic Constraint Optimization**: Guarantees zero overlapping tasks, respects fixed calendar meetings, and enforces working hours and dependencies using CP-SAT integer programming.
4. **Human-in-the-Loop (HITL) Approval**: Halts before consequential operations or calendar modifications; resumes from persisted checkpoints upon explicit human confirmation.
5. **Verified Tool Execution**: Independently verifies every external write before claiming success.
6. **Adaptive Closed-Loop Replanning**: Senses task delays, failures, and emergency calendar shifts, recalculating revised plans while preserving completed work.
7. **Empirical Research Benchmarking**: Built-in evaluation testbed quantitatively comparing Static LLMs, Unweighted Schedulers, and the AURA system.

---

## 2. Mathematical Utility Model

Every candidate task $i$ is assigned a utility score $U(i) \in [0, 1]$ calculated via normalized parameters:

$$U(i) = w_u \cdot U_{\text{urgency}}(i) + w_i \cdot U_{\text{importance}}(i) + w_m \cdot U_{\text{impact}}(i) + w_d \cdot U_{\text{dependency}}(i) + w_e \cdot U_{\text{efficiency}}(i) + B_{\text{mandatory}}(i)$$

Where:
- **Urgency ($U_{\text{urgency}}$)**: Exponential/piecewise linear penalty: $\max\left(0, 1 - \frac{\text{Slack}_i}{\text{Horizon}}\right)$, with $\text{Slack}_i = (\text{Deadline}_i - t) - d_i$.
- **Importance ($U_{\text{importance}}$)**: Normalized from user priority $P_i \in \{1..5\} \rightarrow \frac{P_i - 1}{4}$.
- **Impact ($U_{\text{impact}}$)**: Criticality rating derived from task confidence and priority.
- **Dependency Centrality ($U_{\text{dependency}}$)**: Normalized count of downstream dependent tasks blocked by task $i$.
- **Efficiency ($U_{\text{efficiency}}$)**: Preference for high-yield chunks: $\frac{1}{1 + \ln(1 + d_i / 30)}$.
- **Mandatory Bonus ($B_{\text{mandatory}}$)**: $1.0$ bonus ensuring priority in competitive selection, while hard deadline constraints remain non-negotiable.

Weights are user-configurable in the Settings dashboard and default to:
`urgency: 0.35`, `importance: 0.25`, `impact: 0.15`, `dependency: 0.15`, `efficiency: 0.10`.

---

## 3. System Architecture & Directory Structure

```
aura/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint & lifespans
│   │   ├── api/routes/              # Tasks, Calendar, Plans, Settings, History, Eval
│   │   ├── core/                    # Config, Security, Database engines
│   │   ├── models/                  # SQLAlchemy models (User, Task, Plan, Calendar, Audit)
│   │   ├── schemas/                 # Pydantic V2 schemas with validation
│   │   ├── repositories/            # Repository data access layer
│   │   ├── agents/                  # LangGraph state machine, nodes, utility, optimizer, tools
│   │   ├── integrations/            # LLM provider abstraction & simulated verified calendar
│   │   ├── evaluation/              # Empirical research scenarios and benchmarking runner
│   │   └── db/                      # Database initialization and demo fixtures
│   ├── tests/                       # Pytest suite (utility, optimizer, workflow, api, replan)
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/              # Navbar, StatusBadge, Modals
│   │   ├── pages/                   # Dashboard, Planner, Calendar, Tasks, History, Eval, Settings
│   │   ├── services/                # Typed API client
│   │   ├── types/                   # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AI_WORKFLOW.md
│   ├── EVALUATION.md
│   └── SETUP.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. LangGraph Workflow & Human-in-the-Loop State Machine

```
       [START]
          │
          ▼
     parse_goal  ───────(Ambiguous)──────► ask_clarification ──► [PAUSE / INPUT]
          │                                                              │
          │ (Clear intent)                                               │
          ▼                                                              │
   load_user_context ◄───────────────────────────────────────────────────┘
          │
          ▼
   decompose_tasks
          │
          ▼
   calculate_utility
          │
          ▼
   generate_schedule (Google OR-Tools CP-SAT)
          │
          ▼
   validate_constraints
          │
          ▼
     present_plan
          │
          ▼
   request_approval ───► [INTERRUPT: Human Approval Required]
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

## 5. Quickstart & Local Development

### 5.1 Backend Setup

```bash
# 1. From workspace root, activate virtual environment
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate       # Linux/Mac

# 2. Run backend API server
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation (Swagger UI) is available at: `http://localhost:8000/docs`

### 5.2 Frontend Setup

```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
Frontend Web Dashboard is available at: `http://localhost:5173`

---

## 6. Running Tests & Quality Checks

### 6.1 Backend Tests (Pytest)
```bash
.\.venv\Scripts\pytest.exe backend/tests -v
```
All 11 unit, integration, and workflow tests pass deterministically.

### 6.2 Frontend Tests (Vitest)
```bash
cd frontend
npm test
```
All component and navigation tests pass.

### 6.3 Code Quality & Linting (Ruff & TypeScript)
```bash
# Python
.\.venv\Scripts\ruff.exe check backend --config backend/pyproject.toml

# TypeScript
cd frontend
npm run build
```

---

## 7. Cloud Deployment & Zoho Catalyst Portability

AURA has been strictly designed with clean separation of concerns and database independence:
- **No cloud vendor lock-in**: Core planning, optimization, and state machines are decoupled from proprietary platform APIs.
- **PostgreSQL / SQLite interchangeable**: Runs out-of-the-box locally using async SQLite, and transitions smoothly to PostgreSQL in production via `DATABASE_URL`.
- **Docker Compose provided**: Full stack containerization with PostgreSQL, FastAPI backend, and Nginx frontend.
- **Catalyst Ready**: When cloud deployment is requested, the FastAPI backend maps directly to **Zoho Catalyst AppSail**, with Catalyst Relational Database / PostgreSQL support.
