import logging
from os import getenv
from bot.client import create_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    token = getenv("DISCORD__TOKEN")
    if not token:
        logging.critical("Discord token not found")
        exit(1)

    bot = create_bot()
    bot.run(token, log_handler=None)
