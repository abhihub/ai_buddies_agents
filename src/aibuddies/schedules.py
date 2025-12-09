from typing import List

from .buddies import Buddy


def infer_schedule(buddy: Buddy) -> List[str]:
    """
    Heuristic schedule generator based on persona prompt keywords.
    Not LLM-powered yet; keeps things deterministic.
    """
    prompt = buddy.persona_prompt.lower()

    # Gym/coach
    if any(k in prompt for k in ["gym", "coach", "fitness", "workout", "train"]):
        return [
            "06:00|Good morning. Drink water and do 30-45 mins meditation/mobility.",
            "07:00|Did you finish meditating and hydrate?",
            "14:00|How was lunch? What did you eat?",
            "17:30|Leg day. Start prepping to go to the gym. Drink a smoothie before workout.",
        ]

    # Doctor / health
    if any(k in prompt for k in ["doctor", "medic", "health", "symptom", "care"]):
        return [
            "08:00|Morning wellness check: any symptoms or meds taken?",
            "13:00|Midday check: energy, mood, hydration?",
            "20:00|Evening check: any discomfort today? Plan tomorrow’s rest.",
        ]

    # Finance
    if any(k in prompt for k in ["finance", "budget", "invest", "money", "planner"]):
        return [
            "09:00|Review today’s spending plan.",
            "18:00|Log expenses and note any upcoming bills.",
        ]

    # Tutor
    if any(k in prompt for k in ["tutor", "study", "learn", "physics", "math", "lesson"]):
        return [
            "08:30|Plan today’s study goals.",
            "16:00|Checkpoint: what did you cover? Any blockers?",
            "20:00|Wrap-up: summarize what you learned today.",
        ]

    # Default light cadence
    return [
        "09:00|Morning check-in: priorities for today?",
        "14:00|Midday check-in: progress update?",
        "19:00|Evening wrap-up: what went well, what’s next?",
    ]
