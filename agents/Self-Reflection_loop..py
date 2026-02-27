class ReflectionEngine:

    def reflect(self, agent, task, outcome):

        if outcome["success"]:
            agent.memory.store({"reflection": "strategy worked"})
        else:
            agent.memory.store({"reflection": "adjust hyperparameters"})