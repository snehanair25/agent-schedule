"""
The LangGraph agent: wires together conflict checking, fatigue scoring, and
RAG retrieval into a context-gathering node, then an LLM scoring node that
decides accept / decline / ask_user.
"""

import json
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from agent.state import ScheduleAgentState
from agent.fatigue import compute_fatigue_for_day
from agent.conflict import check_conflict, check_proposed_time
from agent.rag import retrieve_similar_events
from agent.scoring_prompt import build_scoring_prompt

load_dotenv()

import streamlit as st

def _get_groq_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=_get_groq_key())

def gather_context(state: ScheduleAgentState) -> ScheduleAgentState:
    """Runs conflict check, fatigue lookup, and RAG retrieval; fills in state."""
    fatigue = compute_fatigue_for_day(state["day"])

    proposed_time = state.get("proposed_time")

    if proposed_time:
        fits, alt_window, reason = check_proposed_time(
            state["day"], proposed_time, state["duration_hours"]
        )
        has_conflict = not fits
        state["proposed_time_fits"] = fits
        state["suggested_alternative"] = f"{alt_window[0]}-{alt_window[1]}" if alt_window else None
    else:
        has_conflict, window, reason = check_conflict(state["day"], state["duration_hours"])
        state["proposed_time_fits"] = None
        state["suggested_alternative"] = None

    query = f"A {state['category']} event on a {state['day']} with fatigue score {fatigue['fatigue_score']}/10"
    matches = retrieve_similar_events(query, k=3)
    examples = [f"{m.page_content} [decision: {m.metadata['decision']}]" for m in matches]

    state["has_conflict"] = has_conflict
    state["fatigue_score"] = fatigue["fatigue_score"]
    state["retrieved_examples"] = examples
    state["conflict_reason"] = reason
    return state

def score_event(state: ScheduleAgentState) -> ScheduleAgentState:
    """Calls the LLM to decide accept/decline/ask_user based on gathered context."""
    if state["has_conflict"]:
        state["decision"] = "decline"
        state["confidence"] = 1.0
        state["reasoning"] = state.get("conflict_reason", "No valid time slot available.")
        return state

    prompt = build_scoring_prompt(
        event_name=state["event_name"],
        category=state["category"],
        day=state["day"],
        duration_hours=state["duration_hours"],
        fatigue_score=state["fatigue_score"],
        remaining_budget=state.get("remaining_budget", "unknown"),
        conflict_status="No conflict",
        retrieved_examples=state["retrieved_examples"],
        proposed_time=state.get("proposed_time") or "Not specified",
    )

    response = llm.invoke(prompt)
    raw = response.content.strip()

    try:
        parsed = json.loads(raw)
        state["decision"] = parsed["decision"]
        state["confidence"] = float(parsed["confidence"])
        state["reasoning"] = parsed["reasoning"]
    except (json.JSONDecodeError, KeyError):
        state["decision"] = "ask_user"
        state["confidence"] = 0.0
        state["reasoning"] = f"Could not parse model response: {raw[:200]}"

    return state

def route_decision(state: ScheduleAgentState) -> str:
    """Conditional edge: routes based on the decision made in score_event."""
    return state["decision"]

def build_graph():
    graph = StateGraph(ScheduleAgentState)
    graph.add_node("gather_context", gather_context)
    graph.add_node("score_event", score_event)

    graph.set_entry_point("gather_context")
    graph.add_edge("gather_context", "score_event")
    graph.add_conditional_edges(
        "score_event",
        route_decision,
        {"accept": END, "decline": END, "ask_user": END},
    )

    return graph.compile()

if __name__ == "__main__":
    app = build_graph()

    test_event = {
        "event_name": "Dinner with friends",
        "category": "social",
        "day": "Tue",
        "duration_hours": 2.0,
        "remaining_budget": 3.0,
        "proposed_time": "10:00",
    }

    result = app.invoke(test_event)
    print(f"Decision: {result['decision']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reasoning: {result['reasoning']}")