class TelemetryBus:

    def __init__(self):
        self.subscribers = []

    def publish(self, metrics):
        for agent in self.subscribers:
            agent.receive({"type": "telemetry", "payload": metrics})

    def subscribe(self, agent):
        self.subscribers.append(agent)