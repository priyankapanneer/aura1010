from app.agents import nodes
from app.agents.state import AuraState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession


def build_aura_graph(db: AsyncSession):
    """
    Builds the stateful LangGraph workflow for AURA.
    Each node receives the state and the async DB session.
    """
    workflow = StateGraph(AuraState)

    # Wrap node functions to pass db session
    async def n_parse_goal(state: AuraState):
        return await nodes.parse_goal_node(state, db)

    async def n_load_user_context(state: AuraState):
        return await nodes.load_user_context_node(state, db)

    async def n_decompose_tasks(state: AuraState):
        return await nodes.decompose_tasks_node(state, db)

    async def n_calculate_utility(state: AuraState):
        return await nodes.calculate_utility_node(state, db)

    async def n_generate_schedule(state: AuraState):
        return await nodes.generate_schedule_node(state, db)

    async def n_validate_constraints(state: AuraState):
        return await nodes.validate_constraints_node(state, db)

    async def n_present_plan(state: AuraState):
        return await nodes.present_plan_node(state, db)

    async def n_request_approval(state: AuraState):
        return await nodes.request_approval_node(state, db)

    async def n_execute_approved_actions(state: AuraState):
        return await nodes.execute_approved_actions_node(state, db)

    async def n_verify_execution(state: AuraState):
        return await nodes.verify_execution_node(state, db)

    async def n_handle_rejection(state: AuraState):
        return await nodes.handle_rejection_node(state, db)

    # Add Nodes
    workflow.add_node("parse_goal", n_parse_goal)
    workflow.add_node("load_user_context", n_load_user_context)
    workflow.add_node("decompose_tasks", n_decompose_tasks)
    workflow.add_node("calculate_utility", n_calculate_utility)
    workflow.add_node("generate_schedule", n_generate_schedule)
    workflow.add_node("validate_constraints", n_validate_constraints)
    workflow.add_node("present_plan", n_present_plan)
    workflow.add_node("request_approval", n_request_approval)
    workflow.add_node("execute_approved_actions", n_execute_approved_actions)
    workflow.add_node("verify_execution", n_verify_execution)
    workflow.add_node("handle_rejection", n_handle_rejection)

    # Define Conditional Transitions
    def check_ambiguity(state: AuraState) -> str:
        if state.get("is_ambiguous"):
            return END
        return "load_user_context"

    def check_approval(state: AuraState) -> str:
        status = state.get("approval_status", "PENDING").upper()
        if status == "APPROVED":
            return "execute_approved_actions"
        elif status == "REJECTED":
            return "handle_rejection"
        return END  # Pauses at human approval request

    # Graph Edges
    workflow.add_edge(START, "parse_goal")
    workflow.add_conditional_edges("parse_goal", check_ambiguity)
    workflow.add_edge("load_user_context", "decompose_tasks")
    workflow.add_edge("decompose_tasks", "calculate_utility")
    workflow.add_edge("calculate_utility", "generate_schedule")
    workflow.add_edge("generate_schedule", "validate_constraints")
    workflow.add_edge("validate_constraints", "present_plan")
    workflow.add_edge("present_plan", "request_approval")
    workflow.add_conditional_edges("request_approval", check_approval)
    workflow.add_edge("execute_approved_actions", "verify_execution")
    workflow.add_edge("verify_execution", END)
    workflow.add_edge("handle_rejection", END)

    # Checkpoint storage
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app
