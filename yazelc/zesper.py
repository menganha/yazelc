from __future__ import annotations

from abc import abstractmethod
from typing import TypeVar, Optional, Union, Type

import esper

from yazelc.event.event_queue import EventQueue

C = TypeVar('C')
C_alt = TypeVar('C_alt')  # alternative component


class World(esper.World):
    """
    Adds resource management and event queue reference to be used by systems.
    Additional helpful methods are included
    """

    def try_pair_signature(self, ent_1: int, ent_2: int, component_type_1: Type[C], component_type_2: Type[C_alt]) \
            -> Union[tuple[int, C, int, C_alt], tuple[int, C_alt, int, C], None]:
        """
        Checks if the pair have each the corresponding input pair components in the two possible permutations.
        If found returns the entities paired with their respective components
        """
        component_1_1 = self.try_component(ent_1, component_type_1)
        component_2_2 = self.try_component(ent_2, component_type_2)

        component_1_2 = self.try_component(ent_1, component_type_2)
        component_2_1 = self.try_component(ent_2, component_type_1)

        if component_1_1 and component_2_2:
            return ent_1, component_1_1, ent_2, component_2_2
        elif component_1_2 and component_2_1:
            return ent_2, component_2_1, ent_1, component_1_2
        else:
            return None

    def try_signature(self, ent_1: int, ent_2: int, component_type: Type[C]) -> Optional[tuple[int, C, int]]:
        """
        Same as above but only checked on a single entity
        """
        component_1 = self.try_component(ent_1, component_type)
        component_2 = self.try_component(ent_2, component_type)
        if component_1:
            return ent_1, component_1, ent_2
        elif component_2:
            return ent_2, component_2, ent_1
        else:
            return None


# TODO: Remove this class. It only supports the old way of doing things.  Better utilize the processor class defined in
#  the base scene class
class Processor:
    def __init__(self):
        self.priority: int = 0
        self.event_queue = EventQueue()

    @abstractmethod
    def process(self):
        pass
