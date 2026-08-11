"""
Defines the state schema that flows through the LangGraph agent.
Each node reads from and writes to this shared state.
"""

from typing import TypedDict, Optional, List

class ScheduleAgentState(TypedDict):
    # The incoming event being evaluated
    event_name: str
    category: str          # "social", "study", or "campus_event"
    day: str                # "Mon", "Tue", etc.
    duration_hours: float

    # Optional: a specific time the user is proposing
    proposed_time: Optional[str]           # "HH:MM" if specified, else None
    proposed_time_fits: Optional[bool]
    suggested_alternative: Optional[str]   # "HH:MM-HH:MM" string, if proposed time didn't fit
    conflict_reason: Optional[str]

    # Computed during the graph run
    has_conflict: bool
    fatigue_score: float
    remaining_budget: float
    retrieved_examples: List[str]

    # Output of the scoring node
    decision: Optional[str]       # "accept", "decline", or "ask_user"
    confidence: Optional[float]   # 0-1
    reasoning: Optional[str]