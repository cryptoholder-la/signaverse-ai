# formatter_agent.py

class FormatterAgent:

    def format_sample(self, sample):
        return {
            "text": sample.get("text"),
            "sign_pose": sample.get("pose"),
            "emotion": sample.get("emotion", 0)
        }

    def validate_schema(self, sample):
        required = ["text", "sign_pose"]
        return all(key in sample for key in required)