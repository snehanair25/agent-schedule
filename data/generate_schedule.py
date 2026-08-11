"""
Generates a fake college class schedule and saves it as JSON.
This becomes the fixed-constraint input the agent checks new events against.
"""

import json
from pathlib import Path

# Each class: name, days (as weekday abbreviations), start/end in 24hr "HH:MM", location
CLASSES = [
    {
        "course": "ISM 4212 - Systems Analysis",
        "days": ["Mon", "Wed"],
        "start": "09:30",
        "end": "10:45",
        "location": "Hough Hall 120",
    },
    {
        "course": "STA 4210 - Regression Analysis",
        "days": ["Mon", "Wed", "Fri"],
        "start": "11:00",
        "end": "11:50",
        "location": "Turlington 2306",
    },
    {
        "course": "ISM 4323 - Data Analytics",
        "days": ["Mon", "Wed"],
        "start": "12:30",
        "end": "13:45",
        "location": "Hough Hall 250",
    },
    {
        "course": "GEB 4522 - Business Ethics",
        "days": ["Tue", "Thu"],
        "start": "09:30",
        "end": "10:45",
        "location": "Heavener Hall 130",
    },
    {
        "course": "ISM 4930 - AI in Business",
        "days": ["Tue", "Thu"],
        "start": "11:00",
        "end": "12:15",
        "location": "Hough Hall 120",
    },
    {
        "course": "ISM 4930 - AI in Business Lab",
        "days": ["Tue"],
        "start": "12:30",
        "end": "13:20",
        "location": "Hough Hall Lab 101",
    },
    {
        "course": "MAN 4720 - Strategic Management",
        "days": ["Fri"],
        "start": "12:30",
        "end": "15:15",
        "location": "Heavener Hall 240",
    },
]

def build_schedule():
    """Returns the schedule as a flat list of class-day entries, sorted by day/time."""
    entries = []
    for cls in CLASSES:
        for day in cls["days"]:
            entries.append({
                "course": cls["course"],
                "day": day,
                "start": cls["start"],
                "end": cls["end"],
                "location": cls["location"],
            })

    day_order = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4}
    entries.sort(key=lambda e: (day_order[e["day"]], e["start"]))
    return entries

def save_schedule(entries, path="data/class_schedule.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Saved {len(entries)} class entries to {path}")

if __name__ == "__main__":
    schedule = build_schedule()
    save_schedule(schedule)