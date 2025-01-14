from __future__ import annotations

from typing import TypeVar, Optional, Union, Type, Iterator

import esper

from event.event_queue import EventQueue

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

    def remove_all_processors_except(self, *excluded_processor_types: Type[esper.Processor]) -> list[esper.Processor]:
        """ No similar function on the esper Lib."""
        processors_to_remove = [proc for proc in self._processors if type(proc) not in excluded_processor_types]
        for processor in processors_to_remove:
            self._processors.remove(processor)
        return processors_to_remove

    def get_all_processors(self) -> Iterator[Processor]:
        """ Get all processors in current world """
        for processor in self._processors:
            yield processor

    def clear_processors(self):
        self._processors.clear()

    def clear_database(self) -> None:
        super().clear_database()
        self.clear_processors()


class Processor(esper.Processor):
    world: World

    def __init__(self):
        self.event_queue = EventQueue()
