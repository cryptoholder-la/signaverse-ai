class AgentSpawner:

    def spawn(self, parent_agent):

        new_agent = parent_agent.__class__()
        new_agent.persona += " (Evolved)"

        return new_agent