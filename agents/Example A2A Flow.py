registry = AgentRegistry()

data_agent = DataAgent()
training_agent = TrainingAgent()

registry.register(data_agent)
registry.register(training_agent)

a2a = A2AProtocol(registry)

message = {
    "sender": "DataAgent",
    "receiver": "TrainingAgent",
    "task": "retrain_model",
    "payload": {"dataset_id": "asl_44"}
}

data_agent.send(a2a, message)
training_agent.think()