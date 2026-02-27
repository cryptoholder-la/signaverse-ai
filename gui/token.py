class TokenEconomy:

    def __init__(self):
        self.balances = {}

    def reward(self, agent, amount):

        self.balances[agent.name] = \
            self.balances.get(agent.name, 0) + amount

        return self.balances

    def get_balance(self, agent):

        return self.balances.get(agent.name, 0)

    def get_total_balance(self):

        return sum(self.balances.values())

    def get_agent_names(self):

        return list(self.balances.keys())
        