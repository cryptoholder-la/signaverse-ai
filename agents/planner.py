class Planner:

    def plan(self, persona, task):
        if persona == "Performance-Obsessed ML Engineer":
            return {"action": "retrain_model", "priority": "high"}

        if persona == "Skeptical QA Scientist":
            return {"action": "analyze_confusion"}

        return {"action": "noop"}