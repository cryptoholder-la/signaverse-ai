class TaskMarketplace:

    def __init__(self, registry):
        self.registry = registry

    def publish(self, task):

        bids = []

        for agent in self.registry.agents.values():
            confidence = agent.estimate_confidence(task)
            bids.append((agent, confidence))

        best_agent = max(bids, key=lambda x: x[1])[0]
        best_agent.receive(task)