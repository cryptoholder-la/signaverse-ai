class TaskDecomposer:

    def decompose(self, goal):

        if goal["type"] == "increase_accuracy":
            return [
                {"task": "analyze_confusion"},
                {"task": "collect_additional_data"},
                {"task": "hyperparameter_search"},
                {"task": "retrain_model"},
                {"task": "evaluate_model"}
            ]

        return [{"task": "noop"}]