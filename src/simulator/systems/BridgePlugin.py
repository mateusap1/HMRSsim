import esper
import logging

from simulator.typehints.dict_types import SystemArgs


class BridgeProcessor(esper.Processor):
    def __init__(self):
        self.started = False
        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.info("Starting bridge...")
        self.started = True

    def process(self, kwargs: SystemArgs):
        if not self.started:
            self.start()

        pass
