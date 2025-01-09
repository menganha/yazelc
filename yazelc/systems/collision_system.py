from yazelc import zesper
from yazelc.components import Position, Velocity, HitBox, InteractorTag, Sign, Weapon, Health, Collectable, Door
from yazelc.event.events import CollisionEvent, DamageEvent, CollectionEvent, HitDoorEvent, DialogTriggerEvent
from yazelc.player.player import VELOCITY


class CollisionSystem(zesper.Processor):
    """
    Processes collisions with non-moving solid entities

    The system first resolves the collisions between with impenetrable hitbox and all movable hitboxes (independent of
    their impenetrable value) Only after checks for collisions between penetrable hitboxes and adds the corresponding
    event.

    The reasoning is that after a "wall" collision entities normally needs a repositioning which can trigger further
    collision with entities which have been already tested negative for collision. This adds a layer of complexity
    as one has to deal with several collision checks
    """

    def process(self):

        # Resolves collision of all moving hitboxes against impenetrable hitboxes
        impenetrable_hitboxes = [hitbox for ent, hitbox in self.world.get_component(HitBox) if hitbox.impenetrable]
        for ent, (hitbox, position, velocity) in self.world.get_components(HitBox, Position, Velocity):
            colliding_hitboxes_indices = hitbox.collidelistall(impenetrable_hitboxes)
            if colliding_hitboxes_indices:

                if hitbox.skin_depth and len(colliding_hitboxes_indices) == 1:
                    colliding_wall = impenetrable_hitboxes[colliding_hitboxes_indices[0]]
                    self._handle_corner_push(position, velocity, hitbox, colliding_wall, impenetrable_hitboxes)
                elif hitbox.destroy_on_contact:
                    self.world.delete_entity(ent)
                else:
                    self._resolve_collision(position, velocity, hitbox, impenetrable_hitboxes)

        # Everything that it is penetrable it is checked for collision after the movement checks have been resolved
        transparent_hitboxes = [(ent, hb) for ent, hb in self.world.get_component(HitBox) if not hb.impenetrable]
        for index, (ent_1, hitbox_1) in enumerate(transparent_hitboxes):
            rect_dictionary = {ent: hb for ent, hb in transparent_hitboxes[index + 1:]}  # prevents double counting and self checking
            entities_that_collided = hitbox_1.collidedictall(rect_dictionary, 1)
            for ent_2, _ in entities_that_collided:
                self.world.event_queue.add(CollisionEvent(ent_1, ent_2))

    def on_collision(self, collision_event: CollisionEvent):

        # Handles collision when interacting with entities with the Dialog component
        if components := self.world.try_pair_signature(collision_event.ent_1, collision_event.ent_2, InteractorTag,
                                                       Sign
                                                       ):
            _, _, dialog_entity_id, _ = components
            dialog_trigger_event = DialogTriggerEvent(dialog_entity_id)
            self.world.event_queue.add(dialog_trigger_event)
        elif component := self.world.try_signature(collision_event.ent_1, collision_event.ent_2, Collectable):
            collectable_ent_id, collectable, colector_ent_id = component
            collection_event = CollectionEvent(collectable_ent_id, collectable, colector_ent_id)
            self.world.event_queue.add(collection_event)
        elif components := self.world.try_pair_signature(collision_event.ent_1, collision_event.ent_2, Health, Weapon):
            victim_id, _, attacker_id, _ = components
            damage_event = DamageEvent(victim_id, attacker_id)
            self.world.event_queue.add(damage_event)
        elif component := self.world.try_signature(collision_event.ent_1, collision_event.ent_2, Door):
            door_entity_id, _, transversing_entity_id = component
            hit_door_event = HitDoorEvent(door_entity_id, transversing_entity_id)
            self.world.event_queue.add(hit_door_event)

    def _handle_corner_push(self, position: Position, velocity: Velocity, hitbox: HitBox, colliding_wall: HitBox,
                            impenetrable_hitboxes: list[HitBox]):
        """
        Handle case colliding with a corner
        1. Confirm that only one wall is collided with the hitbox
        2. Check collision with the corners of the hitbox. If it doesn't collide don't do anything
        3. Check collision with the 8 reference points. If it collides then don't to anything
        4. Resolve collision in the normal way
        5. Move in the perpendicular direction of movement in the direction oposite to  the obstacle
        """
        colliding_corners = colliding_wall.collidelistall(hitbox.corner_rects)
        collides_with_points = hitbox.collides_with_corner_points(colliding_wall)
        self._resolve_collision(position, velocity, hitbox, impenetrable_hitboxes)
        if colliding_corners and len(colliding_corners) == 1 and not collides_with_points:
            corner_idx = colliding_corners[0]
            if corner_idx == 0:
                if velocity.y < -Velocity.ZERO_THRESHOLD:
                    correction_vel = Velocity(VELOCITY, 0)
                else:
                    correction_vel = Velocity(0, VELOCITY)
            elif corner_idx == 1:
                if velocity.y > Velocity.ZERO_THRESHOLD:
                    correction_vel = Velocity(VELOCITY, 0)
                else:
                    correction_vel = Velocity(0, -VELOCITY)
            elif corner_idx == 2:
                if velocity.y > Velocity.ZERO_THRESHOLD:
                    correction_vel = Velocity(-VELOCITY, 0)
                else:
                    correction_vel = Velocity(0, -VELOCITY)
            else:  # corner_idx == 3:
                if velocity.y < - Velocity.ZERO_THRESHOLD:
                    correction_vel = Velocity(-VELOCITY, 0)
                else:
                    correction_vel = Velocity(0, VELOCITY)
            self._update_entity_position(position, correction_vel, hitbox)

    @staticmethod
    def _update_entity_position(position: Position, velocity: Velocity, hitbox: HitBox):
        """ exact copy of the method in the movement system """
        position.move_ip(velocity.x, velocity.y)
        hitbox.move_ip(round(position.x) - round(position.prev_x), round(position.y) - round(position.prev_y))

    @staticmethod
    def _resolve_collision(position: Position, velocity: Velocity, hitbox: HitBox, impenetrable_hitboxes: list[HitBox]):
        """ Reverts the movement if moving object collides with hitbox """
        for dir_x, dir_y in ((1, 0), (0, 1), (1, 1)):
            delta_x = (round(position.x) - round(position.prev_x)) * dir_x
            delta_y = (round(position.y) - round(position.prev_y)) * dir_y
            test_hitbox = hitbox.move(-delta_x, -delta_y)
            if test_hitbox.collidelist(impenetrable_hitboxes) == -1:
                hitbox.move_ip(-delta_x, -delta_y)
                position.update(round(position.x - velocity.x * dir_x), round(position.y - velocity.y * dir_y))
                break
        else:  # If we cannot resolve then should we signal death (trapped between two walls)?
            raise RuntimeError('Trapped between two impenetrable hitboxes!')
