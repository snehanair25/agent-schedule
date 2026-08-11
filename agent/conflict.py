"""
Checks whether an incoming event can physically fit into a day, given
existing class blocks. Finds free windows between classes and after the
last class, then checks if any window is long enough for the event.
Also supports checking a specific proposed start time against the schedule.
"""

import json
from datetime import datetime

DAY_END = "23:00"   # treat 11pm as the latest an event could reasonably start
MAX_EVENT_HOURS = 4.0   # cap on any single event, regardless of free time available

def _to_minutes(hhmm):
    t = datetime.strptime(hhmm, "%H:%M")
    return t.hour * 60 + t.minute

def _to_hhmm(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

def get_free_windows(day, schedule_path="data/class_schedule.json"):
    """
    Returns a list of (start, end) free windows in 'HH:MM' format for a given day,
    based on gaps between classes and after the last class until DAY_END.
    """
    with open(schedule_path) as f:
        schedule = json.load(f)

    day_classes = [c for c in schedule if c["day"] == day]
    day_classes.sort(key=lambda c: c["start"])

    if not day_classes:
        return [("08:00", DAY_END)]  # whole day free

    windows = []
    for i in range(len(day_classes) - 1):
        gap_start = day_classes[i]["end"]
        gap_end = day_classes[i + 1]["start"]
        if _to_minutes(gap_end) - _to_minutes(gap_start) > 0:
            windows.append((gap_start, gap_end))

    last_end = day_classes[-1]["end"]
    if _to_minutes(DAY_END) > _to_minutes(last_end):
        windows.append((last_end, DAY_END))

    return windows

def check_conflict(day, duration_hours, schedule_path="data/class_schedule.json"):
    """
    Returns (has_conflict, best_window, reason):
      has_conflict: True if the event can't reasonably be scheduled
      best_window: the largest available window as (start, end), or None
      reason: short string explaining the result
    """
    if duration_hours > MAX_EVENT_HOURS:
        return True, None, f"Event duration ({duration_hours}h) exceeds max allowed ({MAX_EVENT_HOURS}h)"

    windows = get_free_windows(day, schedule_path)
    duration_minutes = duration_hours * 60

    fitting_windows = [
        w for w in windows
        if (_to_minutes(w[1]) - _to_minutes(w[0])) >= duration_minutes
    ]

    if not fitting_windows:
        return True, None, "No free window long enough on this day"

    best = max(fitting_windows, key=lambda w: _to_minutes(w[1]) - _to_minutes(w[0]))
    return False, best, "Fits in available window"

def check_proposed_time(day, start_time, duration_hours, schedule_path="data/class_schedule.json"):
    """
    Checks whether a SPECIFIC proposed start time works, given classes that day.
    Returns (fits, alternative_window, reason):
      fits: True if the proposed time works as-is
      alternative_window: best fallback (start, end) if it doesn't fit, else None
      reason: human-readable explanation
    """
    if duration_hours > MAX_EVENT_HOURS:
        return False, None, f"Event duration ({duration_hours}h) exceeds max allowed ({MAX_EVENT_HOURS}h)"

    with open(schedule_path) as f:
        schedule = json.load(f)
    day_classes = [c for c in schedule if c["day"] == day]

    start_min = _to_minutes(start_time)
    end_min = start_min + int(duration_hours * 60)

    if end_min > _to_minutes(DAY_END):
        _, window, _ = check_conflict(day, duration_hours, schedule_path)
        reason = f"Proposed time runs past {DAY_END}"
        reason += f"; {window[0]}-{window[1]} would work instead" if window else "; no valid alternative found"
        return False, window, reason

    for c in day_classes:
        c_start, c_end = _to_minutes(c["start"]), _to_minutes(c["end"])
        if start_min < c_end and end_min > c_start:
            _, window, _ = check_conflict(day, duration_hours, schedule_path)
            reason = f"Conflicts with {c['course']} ({c['start']}-{c['end']})"
            reason += f"; {window[0]}-{window[1]} would work instead" if window else "; no alternative window found"
            return False, window, reason

    return True, (start_time, _to_hhmm(end_min)), "Proposed time works with your schedule"

if __name__ == "__main__":
    has_conflict, window, reason = check_conflict("Tue", 2.0)
    print(f"Tue, 2h event -> conflict: {has_conflict}, window: {window}, reason: {reason}")

    has_conflict, window, reason = check_conflict("Tue", 6.0)
    print(f"Tue, 6h event -> conflict: {has_conflict}, window: {window}, reason: {reason}")

    fits, alt, reason = check_proposed_time("Tue", "10:00", 1.0)
    print(f"Tue 10:00am, 1h -> fits: {fits}, alt: {alt}, reason: {reason}")

    fits, alt, reason = check_proposed_time("Tue", "14:00", 1.0)
    print(f"Tue 2:00pm, 1h -> fits: {fits}, alt: {alt}, reason: {reason}")