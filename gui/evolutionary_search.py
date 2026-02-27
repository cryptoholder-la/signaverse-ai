import random

class EvolutionarySearch:

    def mutate(self, config):

        config["dim"] = random.choice([512, 768, 1024])
        config["num_layers"] = random.choice([6, 8, 12])
        return config

    def crossover(self, config1, config2):

        return {
            "dim": random.choice([config1["dim"], config2["dim"]]),
            "num_layers": random.choice([config1["num_layers"], config2["num_layers"]])
        }

    def mutate_crossover(self, config):

        if random.random() < 0.5:
            return self.mutate(config)
        else:
            return self.crossover(config1=config, config2=config)

        # return self.mutate(config)

        # return self.crossover(config1=config, config2=config)