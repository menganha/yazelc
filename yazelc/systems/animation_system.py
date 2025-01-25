from yazelc import zesper

from yazelc.components import Animation, Renderable
from yazelc.resource_manager import ResourceManager


class AnimationSystem(zesper.Processor):

    def __init__(self, resource_manager: ResourceManager):
        super().__init__()
        self.resource_manager = resource_manager

    def process(self):
        for ent, (animation, renderable) in self.world.get_components(Animation, Renderable):

            image_id = animation.sequence.get_image_id(animation.frame_counter)
            image = self.resource_manager.image(image_id)
            renderable.image = image

            animation.frame_counter += 1

            if animation.frame_counter >= len(animation.sequence.sequence):
                if not animation.sequence.repeat:
                    self.world.remove_component(ent, Animation)
                    continue
                else:
                    animation.frame_counter = 0

