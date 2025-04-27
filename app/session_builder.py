import re

def parse_study_preferences(user_input: str) -> dict:
    study_duration = break_duration = cycles = None

    study_match = re.search(r'study(?:\sfor)?\s*(\\d+)\\s*(?:minutes|min)', user_input, re.IGNORECASE)
    break_match = re.search(r'(?:breaks?|rest(?:\\stime)?)\\s*(?:for|of|:)?\\s*(\\d+)\\s*(?:minutes|min)', user_input, re.IGNORECASE)
    cycle_match = re.search(r'(\\d+)\\s*(?:sessions?|cycles?)', user_input, re.IGNORECASE)

    if study_match:
        study_duration = int(study_match.group(1))
    if break_match:
        break_duration = int(break_match.group(1))
    if cycle_match:
        cycles = int(cycle_match.group(1))

    missing = []
    if not study_duration:
        missing.append("study_duration (in minutes)")
    if not break_duration:
        missing.append("break_duration (in minutes)")
    if not cycles:
        missing.append("cycles (number of study sessions)")

    if missing:
        return {
            "status": "incomplete",
            "message": "Missing required information.",
            "missing_fields": missing
        }

    return {
        "status": "complete",
        "study_duration": study_duration,
        "break_duration": break_duration,
        "cycles": cycles
    }

def build_schedule(study_duration, break_duration, cycles):
    schedule = []
    for i in range(cycles):
        schedule.append(("study", study_duration))
        if i < cycles - 1:
            schedule.append(("break", break_duration))
    return schedule
