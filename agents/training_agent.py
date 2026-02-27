class TrainingAgent(BaseAgent):

    def __init__(self):
        super().__init__("TrainingAgent", PERSONAS["TrainingAgent"])

    def plan(self, task):
        if task["task"] == "retrain_model":
            return self.skills.retrain_model(task["payload"])