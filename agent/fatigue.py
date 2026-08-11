"""
Computes a fatigue score for a given day based on the class schedule.
Fatigue accumulates from: number of classes, total class hours, and short gaps
between classes (which don't allow real recovery time).
"""

import json
from datetime import datetime

def _to_minutes(hhmm):
    """Converts 'HH:MM' string to minutes since midnight."""
    t = datetime.strptime(hhmm, "%H:%M")
    return t.hour * 60 + t.minute

def compute_fatigue_for_day(day, schedule_path="data/class_schedule.json"):
    """
    Returns a dict describing fatigue for a given day (e.g. 'Tue'):
      - num_classes
      - total_class_minutes
      - min_gap_minutes: the shortest gap between consecutive classes
      - fatigue_score: 0-10 scale, higher = more tired
      - last_class_end: 'HH:MM' of when the day's classes end
    """
    with open(schedule_path) as f:
        schedule = json.load(f)

    day_classes = [c for c in schedule if c["day"] == day]
    day_classes.sort(key=lambda c: c["start"])

    if not day_classes:
        return {
            "day": day,
            "num_classes": 0,
            "total_class_minutes": 0,
            "min_gap_minutes": None,
            "fatigue_score": 0,
            "last_class_end": None,
        }

    total_minutes = sum(
        _to_minutes(c["end"]) - _to_minutes(c["start"]) for c in day_classes
    )

    gaps = []
    for i in range(1, len(day_classes)):
        prev_end = _to_minutes(day_classes[i - 1]["end"])
        curr_start = _to_minutes(day_classes[i]["start"])
        gaps.append(curr_start - prev_end)

    min_gap = min(gaps) if gaps else None

    # --- Fatigue scoring logic ---
    # Base: scales with total hours in class (every 60 min ~ 1.2 fatigue points)
    score = (total_minutes / 60) * 1.2

    # Penalty: short gaps mean no real recovery between classes
    for gap in gaps:
        if gap <= 15:
            score += 1.5   # essentially back-to-back
        elif gap <= 30:
            score += 0.75  # short, not much recovery
        # gaps over 30 min: no penalty, treated as real breaks

    # Penalty: more than 3 classes in a day compounds tiredness
    if len(day_classes) >= 4:
        score += 1.5

    score = round(min(score, 10), 2)  # cap at 10

    return {
        "day": day,
        "num_classes": len(day_classes),
        "total_class_minutes": total_minutes,
        "min_gap_minutes": min_gap,
        "fatigue_score": score,
        "last_class_end": day_classes[-1]["end"],
    }

def compute_fatigue_all_days(schedule_path="data/class_schedule.json"):
    """Returns fatigue dicts for all weekdays with classes."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    return [compute_fatigue_for_day(d, schedule_path) for d in days]

if __name__ == "__main__":
    results = compute_fatigue_all_days()
    for r in results:
        print(f"{r['day']}: {r['num_classes']} classes, "
              f"{r['total_class_minutes']}min total, "
              f"min gap {r['min_gap_minutes']}min, "
              f"fatigue score {r['fatigue_score']}/10")