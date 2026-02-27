class RewardEngine:

    def __init__(self):
        self.scores = {}

    def reward(self, agent_name, score):

        if agent_name not in self.scores:
            self.scores[agent_name] = 0

        self.scores[agent_name] += score

    def get_score(self, agent_name):
        return self.scores.get(agent_name, 0)