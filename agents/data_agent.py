from agents.base_agent import BaseAgent
from agents.personas import PERSONAS


class DataAgent(BaseAgent):

    def __init__(self):
        super().__init__("DataAgent", PERSONAS["DataAgent"])

    def plan(self, task):
        if task["task"] == "collect_data":
            return self.skills.scrape_dataset(task["payload"])