from player import MAX_HEALTH
from yazelc import items
from yazelc import zesper
from yazelc.components import Collectable, InteractorTag, Health, Animation, Renderable, Position, Velocity, TweenPosition
from yazelc.event.events import CollectionEvent, HudUpdateEvent, DeleteEntityEvent
from yazelc.tween import TweenFunction
from yazelc.utils.game_utils import Direction


class InventorySystem(zesper.Processor):
    TREASURE_ITEM_TRAVEL_DISTANCE = 15
    TREASURE_TEXTURE_ID = 'TREASURE'
    TREASURE_TILE_SIZE = 16
    TREASURE_ANIMATION_DELAY = 5
    TREASURE_OBJECT_VELOCITY = -1
    TREASURE_OBJECT_ACCELERATION = 0.3
    TREASURE_OBJECT_LIFETIME = 25
    TREASURE_OBJECT_OFFSET = 5

    def __init__(self, player_entity_id: int, inventory: dict[items.CollectableItemType, int]):
        super().__init__()
        self.player_entity_id = player_entity_id
        self.inventory = inventory
        # Here we may include weapons, etc., perhaps some other stuff like how many levels one has passed, etc, i.e., the current
        # state of the player. Or perhaps we should include this in another instance??

    def process(self):
        pass

    def on_collection(self, collection_event: CollectionEvent):

        # Check if the other entity is the players, i.e., no other enemy or moving entity with hitbox can pick up any pickable
        if collection_event.collector_id == self.player_entity_id and not collection_event.collectable.in_chest:  # Is the chest check necessary?
            self._add_pickable(collection_event.collectable, self.player_entity_id)
            self.world.delete_entity(collection_event.collectable_id)

        elif self.world.has_component(collection_event.collector_id, InteractorTag):

            image_strip = self.world.resource_manager.get_animation_strip(self.TREASURE_TEXTURE_ID)
            animation = Animation.from_delay(image_strip, self.TREASURE_ANIMATION_DELAY, one_loop=True)
            renderable = Renderable(image_strip[0])
            self.world.add_component(collection_event.collectable_id, animation)
            self.world.add_component(collection_event.collectable_id, renderable)

            # Add entity with animation of elevating item
            images = items.get_images(self.world, collection_event.collectable.item_type)
            renderable = Renderable(images[0], depth=200)
            object_position = self.world.component_for_entity(collection_event.collectable_id, Position)
            position = Position(object_position.x, object_position.y - self.TREASURE_OBJECT_OFFSET)
            velocity = Velocity()
            tween = TweenPosition(TweenFunction.EASE_OUT_EXPO, Direction.UP, self.TREASURE_ITEM_TRAVEL_DISTANCE,
                                  self.TREASURE_OBJECT_LIFETIME)
            fake_entity_item = self.world.create_entity(position, renderable, velocity, tween)
            self.world.event_queue.add(DeleteEntityEvent(fake_entity_item), self.TREASURE_OBJECT_LIFETIME)

            self._add_pickable(collection_event.collectable, self.player_entity_id)
            self.world.remove_component(collection_event.collectable_id, Collectable)

    def _add_pickable(self, collectable: Collectable, player_ent: int):
        """ Adds pickable to the player inventory"""
        if collectable.item_type == items.CollectableItemType.HEART:
            health = self.world.component_for_entity(player_ent, Health)
            health.points = min(MAX_HEALTH, health.points + collectable.value)
            value = health.points
        else:
            self.inventory[collectable.item_type] += collectable.value
            value = self.inventory[collectable.item_type]

        hud_update_event = HudUpdateEvent(collectable.item_type, value)
        self.world.event_queue.add(hud_update_event)
