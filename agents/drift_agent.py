# drift_agent.py

import numpy as np

class DriftAgent:

    def detect_distribution_shift(self, baseline, current):
        diff = np.abs(np.mean(baseline) - np.mean(current))
        return diff > 0.1

    def trigger_retraining(self, drift_detected):
        return drift_detected