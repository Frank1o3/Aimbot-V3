""" Main entry point for the application. """

import os

from config import Config
from tracker import Tracker

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(os.path.dirname(script_dir), "config.yml")
config = Config.load(config_path)

if __name__ == "__main__":
    bot = Tracker(config)
    bot.run()