from simulator.typehints.component_types import Component


class Inventory(Component):

    def __init__(self, objects: dict = None):
        if objects is None:
            objects = {}
        self.objects = objects

    def __str__(self) -> str:
        return f"Inventory[size={len(self.objects)}] = {self.objects}"
    
    # def __eq__(self, other: "Component"):
    #     if isinstance(other, self.__class__):
    #         if other.objects
