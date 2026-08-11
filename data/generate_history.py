"""
Generates simulated event history over several months: events arrive, get
evaluated against fatigue + weekly allocation budgets, and a decision
(accept/decline) is logged. This becomes the corpus the RAG retriever
searches later.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Allow importing agent/fatigue.py when running this script directly
sys.path.append(str(Path(__file__).resolve().parent.parent))
from agent.fatigue import compute_fatigue_for_day

random.seed(42)  # reproducible simulation

# Weekly allocation budgets, in hours
WEEKLY_ALLOCATIONS = {
    "social": 5,
    "study": 8,
    "campus_event": 3,
}

# Base acceptance probability per category before fatigue/budget adjustments
BASE_ACCEPT_PROB = {
    "social": 0.55,
    "study": 0.75,
    "campus_event": 0.45,
}

EVENT_POOL = {
    "social": ["Dinner with friends", "Roommate hangout", "Birthday party",
               "Coffee catch-up", "Game night", "Off-campus party"],
    "study": ["Study group - stats", "Library session", "Group project meeting",
              "Exam review session", "Tutoring session"],
    "campus_event": ["Guest speaker talk", "Club general meeting", "Career fair",
                      "Volunteer event", "Intramural sports", "Org fundraiser"],
}

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

def simulate_week(week_start_date, fatigue_by_day):
    """Simulates one week of incoming events and decisions. Returns list of event records."""
    remaining = dict(WEEKLY_ALLOCATIONS)  # reset budget each week
    week_events = []

    num_events = random.randint(3, 6)  # how many events land this week

    for _ in range(num_events):
        day = random.choice(WEEKDAYS)
        category = random.choices(
            list(BASE_ACCEPT_PROB.keys()), weights=[0.4, 0.35, 0.25]
        )[0]
        duration = round(random.uniform(1.0, 3.0) if category == "social"
                          else random.uniform(1.0, 2.0), 1)

        fatigue = fatigue_by_day[day]["fatigue_score"]

        # --- Decision probability ---
        prob = BASE_ACCEPT_PROB[category]
        prob -= (fatigue / 10) * 0.35          # more tired -> less likely to accept
        if remaining[category] < duration:
            prob -= 0.5                         # over budget -> much less likely
        prob = max(0.0, min(1.0, prob))

        decision = "accept" if random.random() < prob else "decline"

        energy_cost = None
        enjoyment = None
        if decision == "accept":
            remaining[category] = round(remaining[category] - duration, 1)
            energy_cost = round(duration * (1 + fatigue / 10), 1)
            # lower enjoyment when accepted despite high fatigue
            enjoyment = round(max(1, 5 - fatigue / 3 + random.uniform(-0.5, 0.5)), 1)

        date_str = (week_start_date + timedelta(days=WEEKDAYS.index(day))).strftime("%Y-%m-%d")

        reasoning = (
            f"{'Accepted' if decision == 'accept' else 'Declined'} a {category} event "
            f"('{random.choice(EVENT_POOL[category])}') on a {day} with fatigue score "
            f"{fatigue}/10 and {remaining[category] if decision=='accept' else remaining[category]}h "
            f"{category} budget remaining that week."
        )

        week_events.append({
            "date": date_str,
            "day": day,
            "category": category,
            "duration_hours": duration,
            "fatigue_score": fatigue,
            "decision": decision,
            "energy_cost": energy_cost,
            "enjoyment": enjoyment,
            "reasoning": reasoning,
        })

    return week_events

def generate_history(num_weeks=14, schedule_path="data/class_schedule.json"):
    fatigue_by_day = {r["day"]: r for r in
                       [compute_fatigue_for_day(d, schedule_path) for d in WEEKDAYS]}

    all_events = []
    start = datetime(2026, 1, 12)  # a Monday, semester start

    for w in range(num_weeks):
        week_start = start + timedelta(weeks=w)
        all_events.extend(simulate_week(week_start, fatigue_by_day))

    return all_events

def save_history(events, path="data/event_history.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} simulated events across the semester to {path}")

if __name__ == "__main__":
    events = generate_history()
    save_history(events)

    accepted = sum(1 for e in events if e["decision"] == "accept")
    print(f"{accepted} accepted / {len(events) - accepted} declined out of {len(events)} total")