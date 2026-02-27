class GlobalCoordinator:

    def __init__(self, clusters):
        self.clusters = clusters

    def dispatch(self, task):
        for cluster in self.clusters:
            cluster.broadcast(task)

        return "Task dispatched to all clusters"

    def get_clusters(self):
        return self.clusters

    def get_cluster_names(self):
        return [cluster.region_name for cluster in self.clusters]

    def get_agents(self):
        agents = []

        for cluster in self.clusters:
            for agent in cluster.agents:
                agents.append(agent)

        return agents

    def get_agent_names(self):
        return [agent.name for agent in self.get_agents()]

    def get_agent_count(self):
        return len(self.get_agents())

    def get_cluster_count(self):
        return len(self.clusters)

    def get_task_count(self):
        return sum([len(cluster.agents) for cluster in self.clusters])

    def get_total_task_count(self):
        return sum([len(cluster.agents) for cluster in self.clusters])

    def get_total_agent_count(self):
        return sum([len(cluster.agents) for cluster in self.clusters])



        