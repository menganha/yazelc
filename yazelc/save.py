""" De-serializer for game """
import json
import os
from dataclasses import asdict

from yazelc.resource_manager import ResourceManager
from yazelc.systems.player_system import PlayerState, Inventory

APP_NAME = 'yazelc'


def save_state(inventory: PlayerState, save_file_name):
    app_save_folder = ResourceManager.get_user_path(APP_NAME)
    save_file = os.path.join(app_save_folder, save_file_name)
    with open(save_file, mode='w', encoding='utf-8') as write_file:
        json.dump(asdict(inventory), write_file)


def load_state(save_file_name: str) -> PlayerState:
    app_save_folder = ResourceManager.get_user_path(APP_NAME)
    save_file_path = os.path.join(app_save_folder, save_file_name)
    with open(save_file_path, mode='r', encoding='utf-8') as read_file:
        dictionary = json.load(read_file)
    return PlayerState(Inventory(**dictionary['player_inventory']), dictionary['last_visited_map'])
