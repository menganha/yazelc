import logging

from yazelc import zesper
from yazelc.components import Position, Renderable
from yazelc.utils.game_utils import IVec

logger = logging.getLogger(__name__)


class Camera:
    """
    Renders only what is within the camera border and follows selected entity
    Updates the camera entity to center around the input entity position
    """

    def __init__(self, size: IVec, world_size: IVec):
        self.size = size
        self.world_size = world_size

        self.position = Position()
        self.offset = IVec(0, 0)
        self.ent_id_to_track = None

    def update(self, world: zesper.World):
        if self.ent_id_to_track:
            entity_followed_pos = world.component_for_entity(self.ent_id_to_track, Position)

            self.position.x = entity_followed_pos.x - self.offset.x
            self.position.y = entity_followed_pos.y - self.offset.y

            # Never leave to areas left of above the origin
            self.position.x = max(0.0, self.position.x)
            self.position.y = max(0.0, self.position.y)
            # Never leave to areas right of below the maximum size of the world
            self.position.x = min(float(self.world_size.x - self.size.x), self.position.x)
            self.position.y = min(float(self.world_size.y - self.size.y), self.position.y)

    def track_entity(self, target_entity_id: int, world: zesper.World):
        """
        Sets the offset of the entity to track to be in the center of the camera.
        If target entity has a renderable then center around that, otherwise center around the position
        """
        self.ent_id_to_track = target_entity_id

        if renderable := world.try_component(target_entity_id, Renderable):
            self.offset = IVec(int((self.size.x - renderable.width) / 2), int((self.size.y - renderable.height) / 2))
        elif position := world.try_component(target_entity_id, Position):
            self.offset = IVec(int((self.size.x - position.x) / 2), int((self.size.y - position.y) / 2))
