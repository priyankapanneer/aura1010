# AURA Empirical Evaluation & Research Methodology

## 1. Central Research Question

> **"Does utility-aware adaptive replanning improve task completion and schedule feasibility compared with static LLM planning and conventional constraint-based scheduling?"**

To answer this question quantitatively, AURA includes a reproducible benchmarking testbed (`backend/app/evaluation/`) that subjects planning methodologies to synthetic and real-world stress scenarios.

---

## 2. Compared Methodologies

| Model Identifier | Description | Planning Mechanism | Replanning Capability |
| :--- | :--- | :--- | :--- |
| **Baseline A: Static LLM** | Direct Prompt-to-Schedule | LLM outputs start/end timestamps directly without constraint solver | None (Regenerates entire prompt blindly) |
| **Baseline B: Standard OR-Tools** | Heuristic Constraint Scheduler | OR-Tools CP-SAT with FIFO or fixed priority order; no utility weights | Re-runs solver without adaptive context awareness |
| **Treatment: AURA Full System** | Hybrid LangGraph + Utility + CP-SAT | Normalized multi-factor utility scoring driving OR-Tools CP-SAT | Closed-loop adaptive replanning on slip, failure, or conflicts |

---

## 3. Evaluation Scenarios

1. **Scenario 1: Conflicting Deadlines & Overbooked Capacity**
   - 8 tasks totaling 9 hours of work inside a 6-hour available window.
   - Measures: Graceful degradation, prioritizing high-utility mandatory tasks, identifying unscheduled tasks with actionable explanations.

2. **Scenario 2: Dynamic Task Slippage (Replanning Trigger)**
   - Task 1 takes 90 minutes instead of the estimated 45 minutes, pushing subsequent tasks past fixed meeting boundaries.
   - Measures: Preservation of completed work, minimum schedule disruption, conflict resolution without dropping mandatory tasks.

3. **Scenario 3: Cascading Dependency Ordering**
   - 5 interlinked tasks (A -> B -> C; D -> E) with strict precedence constraints and interspersed meetings.
   - Measures: Zero dependency order violations, optimal slack allocation.

4. **Scenario 4: Unexpected Urgent Interrupt**
   - High-urgency, mandatory 30-minute task inserted mid-day.
   - Measures: Latency to compute revised schedule, least disruption to low-utility optional items.

5. **Scenario 5: Simulated Tool Execution Failure**
   - Calendar booking adapter fails on item 2.
   - Measures: Automated state rollback or retry, safe failure recording, clear user diagnostic.

---

## 4. Quantitative Metrics

- **Feasibility Rate ($\%$)**: Proportion of schedules with zero overlapping blocks, valid working hours, and respected fixed meetings.
- **Hard-Constraint Violation Count**: Occurrences of deadline misses or dependency inversions.
- **Cumulative Weighted Utility ($\Sigma U$)**: Total utility value delivered across scheduled tasks.
- **Replanning Latency (ms)**: Time taken from disruption trigger to feasible revised schedule presentation.
- **Tool Execution Success Rate ($\%$)**: Proportion of verified external writes over attempted writes.
