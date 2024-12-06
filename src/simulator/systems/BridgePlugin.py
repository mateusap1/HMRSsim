import esper
import logging
import threading

from fastapi import FastAPI
from queue import Queue
from typing import Any, Dict

from simulator.typehints.dict_types import SystemArgs

import uvicorn


class BridgeProcessor(esper.Processor):
    def __init__(self):
        self.started = False
        self.logger = logging.getLogger(__name__)
        self.api_thread = None
        self.event_queue = Queue()  # Queue for events
        self.app = FastAPI()  # FastAPI app initialization

        # Set up FastAPI routes inside the processor
        self.app.post("/trigger")(self.trigger_event)

    def trigger_event(self, event: Dict[str, Any]):
        """API endpoint to trigger events."""
        self.event_queue.put(event)  # Add event to the queue
        return {"status": "Event added", "event": event}

    def start_api_server(self):
        """Start the FastAPI server in a separate thread."""

        def run_server():
            uvicorn.run(self.app, host="127.0.0.1", port=8000, log_level="info")

        self.api_thread = threading.Thread(target=run_server, daemon=True)
        self.api_thread.start()

        self.logger.info("API server started on http://127.0.0.1:8000")

    def start(self):
        """Initialize the bridge and start the API server."""

        self.logger.info("Starting bridge...")

        self.start_api_server()
        self.started = True

    def process(self, kwargs: SystemArgs):
        """Process method to handle events from the queue."""

        if not self.started:
            self.start()

        # Consume events from the queue
        while not self.event_queue.empty():
            event = self.event_queue.get_nowait()
            self.logger.info(f"Processing event: {event}")
            # Handle the event in your ECS logic
