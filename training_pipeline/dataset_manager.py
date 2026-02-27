class DatasetManager:
    def __init__(self, version):
        self.version = version

    def load(self):
        path = f"dataset/v{self.version}"
        return load_data(path)