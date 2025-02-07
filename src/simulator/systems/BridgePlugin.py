import json
import esper
import uvicorn
import logging
import threading
import collections

from simpy import FilterStore
from fastapi import FastAPI
from queue import Queue
from typing import Any, Dict, Type, Optional

from simulator.typehints.dict_types import SystemArgs
from simulator.typehints.component_types import Component, EVENT
from simulator.components.Map import Map
from simulator.components.Position import Position
from simulator.components.Velocity import Velocity


logging.getLogger("uvicorn").setLevel(logging.CRITICAL)


class BridgeProcessor(esper.Processor):
    def __init__(self, exposed_components: dict[str, Type[Component]] = None):
        self.started = False
        self.logger = logging.getLogger(__name__)
        self.api_thread = None
        self.event_queue = Queue()  # Queue for events
        self.app = FastAPI()  # FastAPI app initialization

        self.exposed_components = exposed_components
        if self.exposed_components is None:
            self.exposed_components = {
                "map": Map,
                "position": Position,
                "velocity": Velocity,
            }

        # Set up FastAPI routes inside the processor
        self.app.get("/query/{ent}/{component}")(self._query_component)
        self.app.post("/trigger")(self._trigger_event)

    def _get_event_store(self, kwargs: SystemArgs) -> FilterStore:
        event_store = kwargs.get("EVENT_STORE")
        if event_store is None:
            raise ValueError("Can't find Event Store.")

        return event_store

    def _check_event(self, event: Dict[str, Any]) -> str:
        if not "type" in event:
            return 'Trigger data does not contain key "type".'

        if not "payloadName" in event:
            return 'Trigger data does not contain key "payloadName".'

        if not "payload" in event:
            return 'Trigger data does not contain key "payload".'

        if not isinstance(event["payload"], dict):
            return "Payload is not dictionay."

    def _query_component(
        self, ent: int, component: str, attribute: Optional[str] = None
    ):
        result = self._parse_query(ent, component, attribute)
        if result is None:
            return {
                "status": "Error",
                "error": "Ent, component or attribute not found.",
            }, 404

        return result

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
            # log_config = (
            #     uvicorn.config.LOGGING_CONFIG
            # )  # Get Uvicorn's default log config
            # log_config["loggers"]["uvicorn"]["level"] = "CRITICAL"  # Suppress most logs
            # log_config["loggers"]["uvicorn.access"][
            #     "level"
            # ] = "CRITICAL"  # Suppress request logs
            # log_config["loggers"]["uvicorn.error"][
            #     "level"
            # ] = "CRITICAL"  # Suppress error logs

            # uvicorn.run(self.app, host="127.0.0.1", port=8000, log_config=log_config)

            uvicorn.run(self.app, host="127.0.0.1", port=8000)

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

    def _parse_query(
        self, ent: int, component_name: str, attribute: str = None
    ) -> Optional[dict]:
        if not component_name in self.exposed_components:
            return None

        component = self._get_component(ent, self.exposed_components[component_name])
        if component is None:
            return None

        if attribute is not None:
            if not hasattr(component, attribute):
                return None

            return {component_name: {attribute: getattr(component, attribute)}}

        return {component_name: self._serialize(vars(component), in_key=True)}

    def _get_component(self, ent: int, component: Type[Component]) -> Component:
        try:
            return self.world.component_for_entity(ent, component)
        except KeyError:
            return None
        
    def _serialize(self, obj, in_key=False):
        """
        Recursively converts objects into a serializable (and hashable for keys)
        format. When in_key is True, lists are converted to tuples and dictionaries
        are converted to tuples of sorted (key, value) pairs.
        """
        # Base types remain unchanged.
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj

        # For dictionaries, treat keys specially.
        elif isinstance(obj, dict):
            if in_key:
                # Convert dict to a tuple of (key, value) pairs.
                # We sort by the string representation of keys to get a stable order.
                return tuple(
                    (self._serialize(k, in_key=True), self._serialize(v, in_key=True))
                    for k, v in sorted(obj.items(), key=lambda item: repr(item[0]))
                )
            else:
                # In normal values, serialize keys with in_key=True so that they are hashable.
                return {self._serialize(k, in_key=True): self._serialize(v, in_key=False)
                        for k, v in obj.items()}

        # For sequences, if this object is being used as a key, force it to a tuple.
        elif isinstance(obj, (list, set, tuple)):
            serialized_seq = [self._serialize(item, in_key=in_key) for item in obj]
            return tuple(serialized_seq) if in_key else serialized_seq

        # For custom objects, try to use its __dict__.
        elif hasattr(obj, "__dict__"):
            return self._serialize(vars(obj), in_key=in_key)

        else:
            # Fallback: use repr.
            return repr(obj)

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
