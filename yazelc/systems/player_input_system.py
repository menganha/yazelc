import player
from yazelc import zesper
from yazelc.controller import Button
from yazelc.event.events import InputEvent, BlockInputEvent, PauseEvent
from yazelc.menu import menu_box
from yazelc.utils.timer import Timer


class PlayerInputSystem(zesper.Processor):
    """ Uses direct callback to process the input """

    def __init__(self, player_entity_id: int):
        super().__init__()
        self.player_entity_id = player_entity_id
        self.block_timer = Timer()

    def process(self):
        self.block_timer.tick()

    def on_input(self, input_event: InputEvent):
        """ Listener to the input event. Here we can add other methods of entities that react to controller events """
        if self.block_timer.has_finished():
            if input_event.controller.is_button_pressed(Button.START):
                menu_box.create_pause_menu(self.world)
                self.world.event_queue.add(PauseEvent())
            else:
                player.handle_input(input_event, self.player_entity_id, self.world)

    def on_block_input(self, block_input_event: BlockInputEvent):
        self.block_timer.set(block_input_event.block_frames)
