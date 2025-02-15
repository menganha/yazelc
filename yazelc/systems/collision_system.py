import math

from yazelc import zesper
from yazelc.components import Position, HitBox
from yazelc.event.events import eventclass


@eventclass
class EnterCollisionEvent:
    ent_1: int
    ent_2: int


@eventclass
class InCollisionEvent:
    ent_1: int
    ent_2: int


@eventclass
class ExitCollisionEvent:
    ent_1: int
    ent_2: int


@eventclass
class SolidEnterCollisionEvent:
    """ Collision against a solid"""
    ent_solid: int
    ent: int


@eventclass
class SolidExitCollisionEvent:
    ent: int


@eventclass
class HitboxSquishedEvent:
    """ When one cannot resolve a collision it means it is squished between two solids """
    ent: int


class CollisionSystem(zesper.Processor):
    """
    Processes collisions between hitbox

    The system first resolves the collisions between solid hitboxes and all non-solid hitboxes.
    We prevent here any type of "clipping" into the solid world. If a collision is detected we generate a
    "SolidCollisionEvent"

    If no resolution is possible, we generate a "Squished" event. The reason for this name is for when, e.g.,
    the object is between two solid boxes and there's no possible solution of where to position the non-solid
    in between.

    Finally, a second check is performed between non-solid hitboxes. A regular Collision event is generated when
    collision is detected and no resolution is done.

    For all collision types we have also additional events that distinguish between entering, exiting, or being in a
    collision
    """

    def __init__(self, world: zesper.World):
        super().__init__()
        self.world = world
        self.prev_collided_with_solid_entities: set[int] = set()
        self.prev_collided_with_non_solid_entities: set[tuple[int, int]] = set()

    def process(self):

        # Checks between solid and non-solid boxes collisions
        solids = [(ent, hb) for ent, hb in self.world.get_component(HitBox) if hb.solid]
        non_solid = [(ent, hb) for ent, hb in self.world.get_component(HitBox) if not hb.solid]

        collided_with_solid = []
        for ent_s, hb_s in solids:
            for ent, hb in non_solid:
                if hb_s.colliderect(hb):
                    self.event_queue.add(SolidEnterCollisionEvent(ent_s, ent))
                    collided_with_solid.append((hb_s, hb, ent, self.area_of_clip(hb_s, hb)))

        # Resolve first the collisions with bigger overlaps
        for hb_s, hb, ent, _ in sorted(collided_with_solid, key=lambda x: x[-1], reverse=True):
            self.collision_resolution(hb_s, hb, ent)

        # Check for exiting the collision
        collided_with_solid_set = {ent for _, _, ent, _ in collided_with_solid}
        for ent in self.prev_collided_with_solid_entities - collided_with_solid_set:
            self.event_queue.add(SolidExitCollisionEvent(ent))
        self.prev_collided_with_solid_entities = collided_with_solid_set

        # Checks non-solid vs non-solid collisions
        for ent_s, hb_s in solids:
            for ent, hb in non_solid:
                if hb_s.colliderect(hb):
                    self.event_queue.add(HitboxSquishedEvent(ent))

        collided = []
        for idx, (ent_1, hb_1) in enumerate(non_solid):
            for ent_2, hb_2 in non_solid[idx + 1:]:
                if hb_1.colliderect(hb_2):
                    collided_entities = (ent_1, ent_2)
                    if collided_entities in self.prev_collided_with_non_solid_entities:
                        self.event_queue.add(InCollisionEvent(ent_1, ent_2))
                    else:
                        self.event_queue.add(EnterCollisionEvent(ent_1, ent_2))
                    collided.append((ent_1, ent_2))

        for ent_1, ent_2 in self.prev_collided_with_non_solid_entities - set(collided):
            self.event_queue.add(ExitCollisionEvent(ent_1, ent_2))
        self.prev_collided_with_non_solid_entities = set(collided)

    def collision_resolution(self, hitbox_solid: HitBox, hitbox: HitBox, ent: int):
        """
        Resolve collision by checking which axis overlaps less. It pushes the hitbox back on that direction.

        If the collision can be equally resolved on both axes, it resolves by taking precedence on the Y axis, i.e., vertically.
        If a position exists for the input entity, then it uses the direction of movement (except if its diagonal) to select the
        opposite axis for the resolution, e.g., if moving vertically up, it will try to resolve on the horizontal axis.
        """

        side_differences = {
            'l': abs(hitbox.left - hitbox_solid.right),
            'r': abs(hitbox.right - hitbox_solid.left),
            't': abs(hitbox.top - hitbox_solid.bottom),
            'b': abs(hitbox.bottom - hitbox_solid.top),
        }
        minimum_overlap = min(side_differences.values())
        if minimum_overlap == 0:  # Exit early. The collision has been resolved on a previous call
            return

        minimum_sides = sorted(side_differences.keys(), key=lambda x_: side_differences[x_])
        side1, side2 = minimum_sides[:2]

        # If moving on both directions, then do not perform the second side resolution
        position = self.world.try_component(ent, Position)
        if position:
            adv_x = abs(position.prev_x - position.x)
            adv_y = abs(position.prev_y - position.y)
            if math.isclose(adv_x, adv_y):
                side2 = None

        x, y = None, None
        match side1:
            case 'l':
                hitbox.left = hitbox_solid.right
                x = hitbox.x
            case 'r':
                hitbox.right = hitbox_solid.left
                x = hitbox.x
            case 't':
                hitbox.top = hitbox_solid.bottom
                y = hitbox.y
            case 'b':
                hitbox.bottom = hitbox_solid.top
                y = hitbox.y

        # If the second axis of collision is less than the "skin_depth" then slide the hitbox out of this position
        if side2 is not None and side_differences[side2] <= hitbox.skin_depth:
            match side2:
                case 'l':
                    hitbox.left += 1
                    x = hitbox.x
                case 'r':
                    hitbox.right -= 1
                    x = hitbox.x
                case 't':
                    hitbox.top += 1
                    y = hitbox.y
                case 'b':
                    hitbox.bottom -= 1
                    y = hitbox.y

        if position:
            if x is not None:
                position.x = x - hitbox.offset.x  # Double statement is a trick to reset the prev_x attribute
                position.x = x - hitbox.offset.x
            if y is not None:
                position.y = y - hitbox.offset.y
                position.y = y - hitbox.offset.y

    @staticmethod
    def area_of_clip(rect_1: HitBox, rect_2: HitBox) -> int:
        clipped = rect_1.clip(rect_2)
        area = abs(clipped.height * clipped.width)
        return area