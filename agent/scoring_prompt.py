"""
Prompt template for the scoring node — the LLM call that decides whether to
accept, decline, or ask the user about a new event, given fatigue, budget,
and retrieved past patterns.
"""

SCORING_PROMPT = """You are an assistant helping decide whether to accept a new event invitation, based on the user's schedule, energy patterns, and stated priorities.

New event:
- Name: {event_name}
- Category: {category}
- Day: {day}
- Duration: {duration_hours} hours
- Proposed time: {proposed_time}

Current context:
- Fatigue score for this day: {fatigue_score}/10 (higher = more tired, based on class load and gaps between classes)
- Remaining weekly budget for this category: {remaining_budget} hours
- Scheduling conflict check: {conflict_status}

Similar past events and how the user handled them:
{retrieved_examples}

Based on this, decide one of three outcomes:
- "accept": clearly worth doing, low risk of overcommitting
- "decline": clearly not a good fit given fatigue/budget/conflict
- "ask_user": genuinely borderline, the user should decide

Respond in this exact JSON format, with no extra text:
{{
  "decision": "accept" | "decline" | "ask_user",
  "confidence": <float between 0 and 1>,
  "reasoning": "<one or two sentence explanation citing the specific fatigue score, budget, or past pattern that drove this decision>"
}}
"""

def build_scoring_prompt(event_name, category, day, duration_hours,
                          fatigue_score, remaining_budget, conflict_status,
                          retrieved_examples, proposed_time="Not specified"):
    """Fills the template with actual values for a single scoring call."""
    examples_text = "\n".join(f"- {ex}" for ex in retrieved_examples) if retrieved_examples \
        else "No similar past events found."

    return SCORING_PROMPT.format(
        event_name=event_name,
        category=category,
        day=day,
        duration_hours=duration_hours,
        proposed_time=proposed_time,
        fatigue_score=fatigue_score,
        remaining_budget=remaining_budget,
        conflict_status=conflict_status,
        retrieved_examples=examples_text,
    )