class SafetyLayer:

    def validate_task(self, task):

        prohibited = ["delete_dataset", "disable_monitoring"]

        if task["task"] in prohibited:
            return False

        return True
        