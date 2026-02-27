class AgentMemory:

    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.history = []

    def store(self, task):
        self.history.append(task)

    def recall(self, limit=5):
        return self.history[-limit:]