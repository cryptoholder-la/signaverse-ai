import hashlib
import json
import time


class BlockchainLogger:

    def __init__(self):
        self.chain = []

    def log_update(self, update):

        record = {
            "timestamp": time.time(),
            "update": update
        }

        record_hash = hashlib.sha256(
            json.dumps(record).encode()
        ).hexdigest()

        self.chain.append({
            "record": record,
            "hash": record_hash
        })