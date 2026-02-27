import uuid
from agents.memory_store import AgentMemory
from agents.skill_library import SkillLibrary


class BaseAgent:

    def __init__(self, name, persona):
        self.id = str(uuid.uuid4())
        self.name = name
        self.persona = persona
        self.memory = AgentMemory(name)
        self.skills = SkillLibrary()
        self.inbox = []

    def receive(self, message):
        self.inbox.append(message)

    def send(self, protocol, message):
        protocol.route(message)

    def think(self):
        if not self.inbox:
            return None

        task = self.inbox.pop(0)
        self.memory.store(task)

        return self.plan(task)

    def plan(self, task):
        return {"action": "noop", "reason": "no planning logic implemented"}