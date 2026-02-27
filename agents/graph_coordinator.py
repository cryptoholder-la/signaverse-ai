class GraphCoordinator:

    def execute(self, task_graph):

        for node in task_graph.topological_sort():
            assigned_agent = node.agent
            assigned_agent.receive(node.task)