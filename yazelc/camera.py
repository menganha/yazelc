from yazelc import config as cfg
from yazelc import zesper
from yazelc.components import Position, Renderable


# TODO: Adds methods to change smoothly the camera from one position to the other
# TODO: This class may be used migrated to the CameraSystem instead

class Camera:
    """ Max dimensions refer where to the bound where the camera should not go beyond """

    def __init__(self, x_pos: int, y_pos: int, max_x: int = 100, max_y: int = 100):
        self.pos = Position(x_pos, y_pos)
        self.max_pos = Position(max_x, max_y)
        self.offset = Position(max_x, max_y)
        self.ent_id_to_track = None

    def update(self, world: zesper.World):
        if self.ent_id_to_track:
            entity_followed_pos = world.component_for_entity(self.ent_id_to_track, Position)

            self.pos = entity_followed_pos - self.offset

            self.pos.x = max(0, self.pos.x)
            self.pos.y = max(0, self.pos.y)
            self.pos.x = min(self.max_pos.x - cfg.RESOLUTION.x, self.pos.x)
            self.pos.y = min(self.max_pos.y - cfg.RESOLUTION.y, self.pos.y)

    def track_entity(self, ent_id: int, world: zesper.World):
        self.ent_id_to_track = ent_id
        self.offset = self._get_position_of_entity_to_track(ent_id, world)

    @staticmethod
    def _get_position_of_entity_to_track(entity_id_to_follow: int, world: zesper.World) -> Position:
        """
        Used to get the relative position of the entity to track with respect to the camera

        If the tracked entity has a renderable (image) then get the center of that image, otherwise get the position of
        that entity, and if it doesn't have any of the previous two components then return 0,0, i.e., just get a fixed camera
        """
        if renderable := world.try_component(entity_id_to_follow, Renderable):
            return Position(int((cfg.RESOLUTION.x - renderable.width) / 2), int((cfg.RESOLUTION.y - renderable.height) / 2))
        elif position := world.try_component(entity_id_to_follow, Position):
            return Position(int((cfg.RESOLUTION.x - position.x) / 2), int((cfg.RESOLUTION.y - position.y) / 2))
        else:
            return Position(0, 0)
