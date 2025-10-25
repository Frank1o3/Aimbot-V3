""" Main entry point for the application. """

from config import Config
from tracker import Tracker

config = Config()

config.load("config.yml")

if __name__ == "__main__":
    bot = Tracker(config)
    bot.run()