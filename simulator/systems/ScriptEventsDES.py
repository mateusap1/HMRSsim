from typing import NamedTuple, List, Tuple, Callable
from esper import World
from simpy import AnyOf, FilterStore

from main import EVENT
from systems.PathProcessor import EndOfPathTag, EndOfPathPayload

import components.Script as scriptComponent
import systems.GotoDESProcessor as gotoProcessor


ExecutePayload = NamedTuple('ExecuteScriptInstructionPayload', [('ent', int)])
ExecuteInstructionTag = 'ExecuteInstruction'

ExtraInstruction = Tuple[str, Callable[[int, List[str], scriptComponent.Script, FilterStore], scriptComponent.States]]
def init(extra_instructions: List[ExtraInstruction]):
    instruction_set = {t[0]: t[1] for t in extra_instructions}
    print(f'My instruction set: {instruction_set}')

    def process(kwargs):
        # Init
        __event_store = kwargs.get('EVENT_STORE', None)
        __world: World = kwargs.get('WORLD', None)
        env = kwargs.get('ENV', None)
        if __event_store is None:
            raise Exception("Can't find eventStore")
        # On the first run, we put all the scripts in the world in the event queue
        for ent, Script in __world.get_component(scriptComponent.Script):
            payload = ExecutePayload(ent=ent)
            new_event = EVENT(ExecuteInstructionTag, payload)
            __event_store.put(new_event)

        def unblockEntity(ent: int, script: scriptComponent.Script) -> scriptComponent.States:
            script.curr_instruction += 1
            if script.curr_instruction == len(script.instructions):
                script.state = scriptComponent.States.DONE
            else:
                script.state = scriptComponent.States.READY
            return script.state

        # Now we keep checking for pending events and executing them
        watchlist = [ExecuteInstructionTag, EndOfPathTag]
        while True:
            ev = yield __event_store.get(lambda e: e.type in watchlist)
            payload = ev.payload
            script = __world.component_for_entity(payload.ent, scriptComponent.Script)
            if ev.type == ExecuteInstructionTag:
                if script.state != scriptComponent.States.READY:
                    print(f'WARN - Request to execute script not ready')
                i_type, *args = script.instructions[script.curr_instruction].split(' ')
                next_state: scriptComponent.States
                if i_type in instruction_set:
                    next_state = instruction_set[i_type](payload.ent, args, script, __event_store)
                else:
                    print(f'Unkown instrution {i_type}')
                    next_state = scriptComponent.States.READY
                if next_state == scriptComponent.States.READY:
                    payload = ExecutePayload(payload.ent)
                    new_event = EVENT(ExecuteInstructionTag, payload)
                    __event_store.put(new_event)
            elif ev.type == EndOfPathTag:
                ent, timestamp = payload
                if ev.type not in script.expecting:
                    print(f'WARN - Was not expecting {ev.type}')
                else:
                    script.expecting.remove(EndOfPathTag)
                    if not script.expecting:
                        r = unblockEntity(ent, script)
                        if r == scriptComponent.States.READY:
                            payload = ExecutePayload(ent=ent)
                            new_event = EVENT(ExecuteInstructionTag, payload)
                            __event_store.put(new_event)

            else:
                print(f'Got event {ev.type}')

    return process
