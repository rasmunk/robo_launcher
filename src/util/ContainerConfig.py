import json


# the config member is expected to implement an __iter__ definition
class ContainerConfig:
    config = None

    def __init__(self, config):
        self.config = config
