import math

from yazelc import zesper
from yazelc.components import Position, HitBox, Move
from yazelc.event.events import eventclass


@eventclass
class EndMovementEvent:
    ent: int


class MovementSystem(zesper.Processor):

    def process(self):
        """
        Moves all entities with positions. If it has a Hitbox component then updates their internal position as well.
        For accelerated entities it limits their minimal velocity.
        """

        # for ent, (velocity, acceleration) in self.world.get_components(Velocity, Acceleration):
        #     velocity.x = max(velocity.x + acceleration.x, Velocity.ZERO_THRESHOLD)
        #     velocity.y = max(velocity.y + acceleration.x, Velocity.ZERO_THRESHOLD)
        #
        # for ent, (velocity, position) in self.world.get_components(Velocity, Position):
        #     position.move_ip(velocity.x, velocity.y)
        #
        #     if hitbox := self.world.try_component(ent, HitBox):
        #         hitbox.move_ip(round(position.x) - round(position.prev_x), round(position.y) - round(position.prev_y))
        #
        # # TODO: Make a limit here for movement outside the world bounds

        for ent, (move, position) in self.world.get_components(Move, Position):
            hitbox = self.world.try_component(ent, HitBox)
            if move.time_steps == -1:
                x = (move.goal.x - position.x)
                y = (move.goal.y - position.y)
                abs_r = math.sqrt(x ** 2 + y ** 2)
                move.vel_x = move.velocity * x / abs_r
                move.vel_y = move.velocity * y / abs_r
                move.time_steps = int(abs_r / move.velocity)

            elif move.time_steps == 0:
                position.x = move.goal.x
                position.y = move.goal.y
                if hitbox:
                    hitbox.x = position.x
                    hitbox.y = position.y
                self.world.remove_component(ent, Move)
                self.event_queue.add(EndMovementEvent(ent))

            else:
                position.x += move.vel_x
                position.y += move.vel_y
                if hitbox:
                    hitbox.x = position.x
                    hitbox.y = position.y
                move.time_steps -= 1
