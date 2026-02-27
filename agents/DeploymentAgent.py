class DeploymentAgent(BaseAgent):

    def __init__(self):
        super().__init__("DeploymentAgent", PERSONAS["DeploymentAgent"])

    def plan(self, task):
        if task["task"] == "deploy":
            return self.skills.deploy_model(task["payload"])