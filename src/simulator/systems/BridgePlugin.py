import esper
import uvicorn
import logging
import threading
import collections

from simpy import FilterStore
from fastapi import FastAPI
from queue import Queue
from typing import Any, Dict

from simulator.typehints.dict_types import SystemArgs
from simulator.typehints.component_types import EVENT


class BridgeProcessor(esper.Processor):
    def __init__(self):
        self.started = False
        self.logger = logging.getLogger(__name__)
        self.api_thread = None
        self.event_queue = Queue()  # Queue for events
        self.app = FastAPI()  # FastAPI app initialization

        # Set up FastAPI routes inside the processor
        self.app.post("/trigger")(self._trigger_event)

    def _get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE")
        if event_store is None:
            raise ValueError("Can't find Event Store.")
        
        return event_store

    def _check_event(self, event: Dict[str, Any]) -> str:
        if not "type" in event:
            return "Trigger data does not contain key \"type\"."
        
        if not "payloadName" in event:
            return "Trigger data does not contain key \"payloadName\"."
        
        if not "payload" in event:
            return "Trigger data does not contain key \"payload\"."
        
        if not isinstance(event["payload"], dict):
            return "Payload is not dictionay."

    def _trigger_event(self, event: Dict[str, Any]):
        """API endpoint to trigger events."""
        error = self._check_event(event)
        if error:
            return {"status": "Error", "error": error}, 400

        self.event_queue.put(event)  # Add event to the queue
        return {"status": "Event added", "event": event}

    def _start_api_server(self):
        """Start the FastAPI server in a separate thread."""

        def run_server():
            uvicorn.run(self.app, host="127.0.0.1", port=8000, log_level="info")

        self.api_thread = threading.Thread(target=run_server, daemon=True)
        self.api_thread.start()

        self.logger.info("API server started on http://127.0.0.1:8000")

    def _parse_event(self, event: Dict[str, Any]) -> EVENT:
        event_type: Dict = event["type"]
        payload_name: Dict = event["payloadName"]
        payload_data: Dict = event["payload"]

        PayloadType = collections.namedtuple(payload_name, payload_data.keys())
        payload = PayloadType(*payload_data.values())
        
        return EVENT(type=event_type, payload=payload)

    def start(self):
        """Initialize the bridge and start the API server."""

        self.logger.info("Starting bridge...")

        self._start_api_server()
        self.started = True

    def process(self, kwargs: SystemArgs):
        """Process method to handle events from the queue."""
        event_store = self._get_event_store(kwargs)

        if not self.started:
            self.start()

        # Consume events from the queue
        while not self.event_queue.empty():
            event_data = self.event_queue.get_nowait()
            self.logger.info(f"Processing event: {event_data}")

            event = self._parse_event(event_data)
            self.logger.info(f"Parsed event: {event}")
            event_store.put(event)

            # Handle the event in your ECS logic

    def clean(self):
        self.api_thread.join(timeout=1)
