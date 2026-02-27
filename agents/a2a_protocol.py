class A2AProtocol:

    def __init__(self, registry):
        self.registry = registry

    def route(self, message):
        receiver = self.registry.get(message["receiver"])
        if receiver:
            receiver.receive(message)