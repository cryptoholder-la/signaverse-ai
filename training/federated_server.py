# training/federated_server.py

import torch


class FederatedServer:

    def __init__(self, global_model):
        self.global_model = global_model

    def aggregate(self, client_weights):

        new_weights = {}

        for key in self.global_model.state_dict().keys():
            new_weights[key] = sum(
                client[key] for client in client_weights
            ) / len(client_weights)

        self.global_model.load_state_dict(new_weights)

        return self.global_model.state_dict()