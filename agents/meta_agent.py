class MetaAgent:

    def __init__(self, registry, decomposer, marketplace):
        self.registry = registry
        self.decomposer = decomposer
        self.marketplace = marketplace

    def receive_global_goal(self, goal):
        subtasks = self.decomposer.decompose(goal)

        for task in subtasks:
            self.marketplace.publish(task)