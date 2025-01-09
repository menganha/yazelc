from yazelc import zesper
from yazelc.event.events import DeleteEntityEvent


class DelayedEntityRemovalSystem(zesper.Processor):
    """
    Event listener Removes entities when receiving the event with a potential delay
    """

    def process(self):
        pass

    def on_delete_entity(self, delete_entity_event: DeleteEntityEvent):
        self.world.delete_entity(delete_entity_event.entity_id)
