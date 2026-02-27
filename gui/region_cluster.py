class RegionCluster:

    def __init__(self, region_name):
        self.region_name = region_name
        self.agents = []

    def register(self, agent):
        self.agents.append(agent)

    def broadcast(self, task):
        for agent in self.agents:
            agent.receive(task)

        print(f"Broadcasted task to {self.region_name}: {task}")

        return f"Task broadcasted to {self.region_name}"

    def get_agent_names(self):
        return [agent.name for agent in self.agents]

    def get_agent_count(self):
        return len(self.agents)

    def get_region_name(self):
        return self.region_name
        