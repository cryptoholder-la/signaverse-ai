class MPMProtocol:

    def __init__(self, registry):
        self.registry = registry

    def send_internal(self, message):
        self.registry.get(message["receiver"]).receive(message)

    def send_rest(self, message):
        print("Sending via REST:", message)

    def send_websocket(self, message):
        print("Streaming message:", message)

    def send_ray(self, message):
        print("Dispatching Ray task:", message)