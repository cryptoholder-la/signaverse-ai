class EvaluationAgent(BaseAgent):

    def __init__(self):
        super().__init__("EvaluationAgent", PERSONAS["EvaluationAgent"])

    def plan(self, task):
        if task["task"] == "evaluate":
            return self.skills.analyze_confusion(task["payload"])