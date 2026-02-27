class CleanerAgent:

    def remove_low_quality(self, dataset):
        return [
            sample for sample in dataset
            if sample.confidence > 0.8
        ]