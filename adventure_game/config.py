"""
Configuration global variables
"""
TILE_SIZE = 32
DIS_WIDTH = 640
DIS_HEIGHT = 480
WORLD_WIDTH = DIS_WIDTH
WORLD_HEIGTH = DIS_HEIGHT - TILE_SIZE
UI_WIDTH = DIS_WIDTH
UI_HEIGHT = TILE_SIZE
SCALE = 2

WHITE = (255, 255, 240)
YELLOW = (255, 255, 102)
BLACK = (0, 0, 0)
RED = (213, 50, 80)
RED_T = (213, 50, 80, 90)
GREEN = (0, 255, 0)
BLUE = (50, 153, 213)
GRAY = (50, 60, 57)

FRAMERATE = 60
VELOCITY = 2*FRAMERATE
SCROLL_VELOCITY = 8*FRAMERATE
SPRITE_SIZE = 32
SWORD_HITBOX = 8
BLINK_TIME = 25
COOLDOW_TIME_PLAYER = 35
