from random import choice, random

import pygame

from yazelc import zesper
from yazelc.components import Brain, State, Velocity, Animation, Enemy, Position, Weapon, HitBox, Renderable
from yazelc.event.events import EnemyDecisionEvent
from yazelc.utils.game_utils import Direction, Status


class AISystem(zesper.Processor):

    def process(self):
        for ent, (brain, state) in self.world.get_components(Brain, State):
            state.update()

            if brain.block_timer.is_set():
                if brain.block_timer.has_finished():
                    brain.block_timer.set(0)
                    brain.timer.end()
                brain.block_timer.tick()

            if brain.timer.has_finished() and not brain.block_timer.is_set():
                brain.timer.reset()
                self.world.event_queue.add(EnemyDecisionEvent(ent, brain.behaviour_type))

            brain.timer.tick()

    def on_enemy_decision(self, enemy_decision_event: EnemyDecisionEvent):
        """ One of several more behaviors for enemies """

        state = self.world.component_for_entity(enemy_decision_event.enemy_id, State)
        velocity = self.world.component_for_entity(enemy_decision_event.enemy_id, Velocity)

        direction_choices = list(Direction)[:4]
        state.direction = choice(direction_choices)
        next_status = Status.IDLE if random() < 0.3 else Status.WALKING  # TODO: Do we need statuses at all????!!
        state.status = next_status

        # This considers all enemies have animations!
        enemy_type = self.world.component_for_entity(enemy_decision_event.enemy_id, Enemy).type
        animation_identifier = self.world.resource_manager.get_animation_identifier(enemy_type, state.status, state.direction)
        animation_strip = self.world.resource_manager.get_animation_strip(animation_identifier)
        # TODO: This is hardcoded. Berrry bad! Maybe include the frame information on the animation stripe
        animation = Animation.from_delay(animation_strip, 10)
        self.world.add_component(enemy_decision_event.enemy_id, animation)
        if enemy_type == 'kefer' and state.status == Status.IDLE:
            position = self.world.component_for_entity(enemy_decision_event.enemy_id, Position)
            self.create_projectile(position, state.direction)

        if state.status == Status.WALKING:
            velocity.x = state.direction.value.x
            velocity.y = state.direction.value.y
        else:
            velocity.x = 0
            velocity.y = 0

    # TODO: Move this to the enemy class
    def create_projectile(self, position: Position, direction: Direction):
        projectile_ent = self.world.create_entity()
        velocity = Velocity(direction.value.x * 1, direction.value.y * 1)
        position_projectile = Position(position.x, position.y)

        self.world.add_component(projectile_ent, Weapon(1, -1, 7, 3))
        self.world.add_component(projectile_ent, HitBox(int(position.x), int(position.y), 5, 5, destroy_on_contact=True))
        self.world.add_component(projectile_ent, position_projectile)
        self.world.add_component(projectile_ent, velocity)
        self.world.add_component(projectile_ent, Enemy('projectile'))
        surface = pygame.Surface((5, 5))
        pygame.draw.rect(surface, config.C_RED, surface.get_rect(), width=1, border_radius=1)
        self.world.add_component(projectile_ent, Renderable(surface))
