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

    def __init__(self):
        super().__init__()
        self.prev_collided_with_solid_entities: set[int] = set()
        self.prev_collided_with_non_solid_entities: set[tuple[int, int]] = set()

    def process(self):

        # Checks between solid and non-solid boxes
        solids = [(ent, hb) for ent, hb in self.world.get_component(HitBox) if hb.solid]
        non_solid = [(ent, hb) for ent, hb in self.world.get_component(HitBox) if not hb.solid]

        collided_with_solid = []
        for ent_s, hb_s in solids:
            for ent, hb in non_solid:
                if hb_s.colliderect(hb):
                    self.event_queue.add(SolidEnterCollisionEvent(ent_s, ent))
                    collided_with_solid.append(ent)
                    self.collision_resolution(hb_s, hb, ent)

        for ent in self.prev_collided_with_solid_entities - set(collided_with_solid):
            self.event_queue.add(SolidExitCollisionEvent(ent))
        self.prev_collided_with_solid_entities = set(collided_with_solid)

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
        Resolves collision taking precedence on the Y axis, i.e., if the collision can be resolved by pushing
        either horizontally or vertically the box, it will resolve it vertically

        If a position exists for the input entity, then it uses the direction to choose the pushing
        """

        position = self.world.try_component(ent, Position)

        side_differences = {
            'l': abs(hitbox.left - hitbox_solid.right),
            'r': abs(hitbox.right - hitbox_solid.left),
            't': abs(hitbox.top - hitbox_solid.bottom),
            'b': abs(hitbox.bottom - hitbox_solid.top),
        }
        minimum_overlap = min(side_differences.values())
        minimum_sides = [side for side in side_differences if side_differences[side] == minimum_overlap]
        if len(minimum_sides) > 1:
            if position and (abs(position.prev_x - position.x) < abs(position.prev_y - position.y)):
                weight = ('l', 'r')
            else:
                weight = ('t', 'b')
            side = sorted(minimum_sides, key=lambda x: 0 if x in weight else 1)[0]
        else:
            side = minimum_sides[0]

        x, y = None, None
        if side == 'l':
            hitbox.left = hitbox_solid.right
            x = hitbox.x
        elif side == 'r':
            hitbox.right = hitbox_solid.left
            x = hitbox.x
        elif side == 't':
            hitbox.top = hitbox_solid.bottom
            y = hitbox.y
        else:
            hitbox.bottom = hitbox_solid.top
            y = hitbox.y

        if position:
            if x is not None:
                position.x = x
            else:
                position.y = y

    def on_collision(self, collision_event: EnterCollisionEvent):
        # TODO: Move this to each system independently!!!!!! We are coupling too much stuff here!!!!
        # Handles collision when interacting with entities with the Dialog component
        # if components := self.world.try_pair_signature(collision_event.ent_1, collision_event.ent_2, InteractorTag, Sign ):
        #     _, _, dialog_entity_id, _ = components
        #     dialog_trigger_event = DialogTriggerEvent(dialog_entity_id)
        #     self.event_queue.add(dialog_trigger_event)
        # elif component := self.world.try_signature(collision_event.ent_1, collision_event.ent_2, Collectable):
        #     collectable_ent_id, collectable, colector_ent_id = component
        #     collection_event = CollectionEvent(collectable_ent_id, collectable, colector_ent_id)
        #     self.event_queue.add(collection_event)
        # elif components := self.world.try_pair_signature(collision_event.ent_1, collision_event.ent_2, Health, Weapon):
        #     victim_id, _, attacker_id, _ = components
        #     damage_event = DamageEvent(victim_id, attacker_id)
        #     self.event_queue.add(damage_event)
        # elif component := self.world.try_signature(collision_event.ent_1, collision_event.ent_2, Door):
        #     door_entity_id, _, transversing_entity_id = component
        #     hit_door_event = HitDoorEvent(door_entity_id, transversing_entity_id)
        #     self.event_queue.add(hit_door_event)
        pass
