"""
Streamlit UI for the schedule agent. Submit a new event, see the agent's
decision along with the reasoning, fatigue context, and retrieved past
patterns that informed it.
"""

import json
import streamlit as st
from agent.graph import build_graph
from agent.fatigue import compute_fatigue_for_day

st.set_page_config(page_title="Schedule Agent", page_icon="🔋", layout="centered")

# --- Design tokens: an "energy budget" theme, since this is literally about social battery ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
    --bg: #161B26;
    --surface: #1F2735;
    --surface-2: #262F40;
    --text: #EDEFF5;
    --text-muted: #9AA5B8;
    --gold: #E8A94C;
    --teal: #5FB3A3;
    --coral: #E2685A;
    --lavender: #8B85C1;
}

.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: 'IBM Plex Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}

[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--surface-2);
}

[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--surface-2);
    border-radius: 12px;
    padding: 1.75rem;
}

.stTextInput input, .stSelectbox [data-baseweb="select"] > div {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border-color: transparent !important;
    border-radius: 8px !important;
}

.stButton button, .stFormSubmitButton button {
    background: var(--gold) !important;
    color: #161B26 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

.stButton button:hover, .stFormSubmitButton button:hover {
    background: #f0bb6a !important;
}

/* battery gauge */
.battery-row { margin-bottom: 1.1rem; }
.battery-label {
    display: flex; justify-content: space-between; align-items: baseline;
    font-size: 0.85rem; margin-bottom: 0.3rem;
}
.battery-label .name { color: var(--text); font-weight: 600; }
.battery-label .hours { color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif; }
.battery-shell {
    display: flex; align-items: center; height: 20px;
}
.battery-body {
    flex-grow: 1; height: 18px; background: var(--surface-2);
    border-radius: 5px; overflow: hidden; position: relative;
}
.battery-fill {
    height: 100%; border-radius: 5px 0 0 5px;
    transition: width 0.4s ease;
}
.battery-nub {
    width: 4px; height: 9px; background: var(--surface-2);
    margin-left: 2px; border-radius: 0 2px 2px 0;
}

/* decision banner */
.decision-banner {
    border-radius: 10px; padding: 1rem 1.25rem; margin: 1rem 0 0.75rem 0;
    display: flex; align-items: center; gap: 0.75rem;
}
.decision-banner .icon { font-size: 1.4rem; }
.decision-banner .label { font-weight: 600; font-size: 1.05rem; font-family: 'Fraunces', serif; }
.decision-banner .conf { color: var(--text-muted); font-size: 0.85rem; margin-left: auto; }

.reasoning-text {
    color: var(--text-muted); font-size: 0.95rem; line-height: 1.5;
    padding: 0 0.1rem;
}
</style>
""", unsafe_allow_html=True)

DEFAULT_SPLIT = {"study": 0.45, "social": 0.275, "campus_event": 0.275}
WAKING_HOURS_PER_WEEK = 16 * 7  # 7am-11pm, 7 days
TA_JOB_HOURS_PER_WEEK = 10.0


def compute_default_budgets(split=None, schedule_path="data/class_schedule.json"):
    """
    Computes weekly category budgets from actual discretionary time:
    waking hours minus class time minus TA job hours, split by category percentage.
    """
    if split is None:
        split = DEFAULT_SPLIT

    with open(schedule_path) as f:
        schedule = json.load(f)

    total_class_minutes = sum(
        (int(c["end"][:2]) * 60 + int(c["end"][3:])) -
        (int(c["start"][:2]) * 60 + int(c["start"][3:]))
        for c in schedule
    )
    total_class_hours = total_class_minutes / 60
    discretionary_hours = max(0, WAKING_HOURS_PER_WEEK - total_class_hours - TA_JOB_HOURS_PER_WEEK)

    budgets = {cat: round(discretionary_hours * pct, 1) for cat, pct in split.items()}
    return budgets, total_class_hours, discretionary_hours


DEFAULT_BUDGETS, TOTAL_CLASS_HOURS, DISCRETIONARY_HOURS = compute_default_budgets()

CATEGORY_LABELS = {"study": "Study", "social": "Social", "campus_event": "Campus Event"}
DECISION_STYLE = {
    "accept": {"color": "var(--teal)", "bg": "rgba(95,179,163,0.15)", "icon": "✓", "label": "Accept"},
    "decline": {"color": "var(--coral)", "bg": "rgba(226,104,90,0.15)", "icon": "✕", "label": "Decline"},
    "ask_user": {"color": "var(--lavender)", "bg": "rgba(139,133,193,0.15)", "icon": "?", "label": "Ask you"},
}

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
if "remaining_budget" not in st.session_state:
    st.session_state.remaining_budget = dict(DEFAULT_BUDGETS)
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.title("🔋 Schedule Agent")
st.caption("Submit a new event and see how it fits your week.")

# --- Sidebar: battery-style budget gauges ---
with st.sidebar:
    st.header("This week's charge")
    st.caption(f"{DISCRETIONARY_HOURS:.0f}h discretionary time "
               f"({TOTAL_CLASS_HOURS:.0f}h in class, {TA_JOB_HOURS_PER_WEEK:.0f}h TA job)")

    for cat, remaining in st.session_state.remaining_budget.items():
        total = DEFAULT_BUDGETS[cat]
        pct = max(0.0, min(1.0, remaining / total)) if total > 0 else 0.0

        if pct > 0.6:
            fill_color = "var(--teal)"
        elif pct > 0.3:
            fill_color = "var(--gold)"
        else:
            fill_color = "var(--coral)"

        st.markdown(f"""
        <div class="battery-row">
            <div class="battery-label">
                <span class="name">{CATEGORY_LABELS[cat]}</span>
                <span class="hours">{remaining:.1f}h / {total:.1f}h</span>
            </div>
            <div class="battery-shell">
                <div class="battery-body">
                    <div class="battery-fill" style="width:{pct*100:.0f}%; background:{fill_color};"></div>
                </div>
                <div class="battery-nub"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Reset week", use_container_width=True):
        st.session_state.remaining_budget = dict(DEFAULT_BUDGETS)
        st.session_state.history = []
        st.session_state.last_result = None
        st.rerun()

# --- Main form ---
with st.form("event_form"):
    event_name = st.text_input("Event name", placeholder="e.g. Dinner with friends")
    category = st.selectbox("Category", ["social", "study", "campus_event"],
                             format_func=lambda c: CATEGORY_LABELS[c])
    day = st.selectbox("Day", ["Mon", "Tue", "Wed", "Thu", "Fri"])
    duration_hours = st.slider("Duration (hours)", 0.5, 6.0, 2.0, step=0.5)
    propose_time = st.checkbox("Propose a specific start time")
    proposed_time_input = st.time_input("Start time", disabled=not propose_time) if propose_time else None
    submitted = st.form_submit_button("Evaluate event", use_container_width=True)

if submitted:
    if not event_name.strip():
        st.error("Please enter an event name.")
    else:
        with st.spinner("Evaluating against your schedule and patterns..."):
            result = st.session_state.graph.invoke({
                "event_name": event_name,
                "category": category,
                "day": day,
                "duration_hours": duration_hours,
                "remaining_budget": st.session_state.remaining_budget[category],
                "proposed_time": proposed_time_input.strftime("%H:%M") if proposed_time_input else None,
            })

        if result["decision"] == "accept":
            st.session_state.remaining_budget[category] = round(
                max(0, st.session_state.remaining_budget[category] - duration_hours), 1
            )

        st.session_state.last_result = {
            "event_name": event_name,
            "category": category,
            "day": day,
            "duration_hours": duration_hours,
            "decision": result["decision"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "fatigue_score": result["fatigue_score"],
            "examples": result.get("retrieved_examples", []),
        }

        st.session_state.history.append({
            "event": event_name, "category": CATEGORY_LABELS[category], "day": day,
            "decision": result["decision"], "confidence": result["confidence"],
        })

        st.rerun()

# --- Result display ---
if st.session_state.last_result:
    r = st.session_state.last_result
    style = DECISION_STYLE[r["decision"]]

    st.markdown(f"""
    <div class="decision-banner" style="background:{style['bg']}; border:1px solid {style['color']};">
        <span class="icon" style="color:{style['color']};">{style['icon']}</span>
        <span class="label" style="color:{style['color']};">{style['label']}</span>
        <span class="conf">{r['confidence']:.0%} confidence</span>
    </div>
    <div class="reasoning-text">{r['reasoning']}</div>
    """, unsafe_allow_html=True)

    with st.expander("Why this decision? See the context the agent used"):
        fatigue_detail = compute_fatigue_for_day(r["day"])
        st.write(f"**Fatigue score for {r['day']}:** {r['fatigue_score']}/10")
        st.write(
            f"{fatigue_detail['num_classes']} classes, "
            f"{fatigue_detail['total_class_minutes']} min total, "
            f"shortest gap {fatigue_detail['min_gap_minutes']} min"
        )
        st.write(f"**{CATEGORY_LABELS[r['category']]} budget remaining now:** "
                  f"{st.session_state.remaining_budget[r['category']]:.1f}h")

        st.write("**Similar past events retrieved:**")
        if r["examples"]:
            for ex in r["examples"]:
                st.write(f"- {ex}")
        else:
            st.write("No similar past events found.")

# --- Session history ---
if st.session_state.history:
    st.divider()
    st.subheader("This session")
    st.dataframe(st.session_state.history, use_container_width=True)