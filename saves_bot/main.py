import asyncio
import logging
import os
import sys

import dotenv

from saves_bot.bot import SavesBot


def main():
    logging.basicConfig(
        format='[%(asctime)s] [%(threadName)s/%(levelname)s] [%(filename)s:%(lineno)i]: %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO
    )
    dotenv.load_dotenv()
    TOKEN = os.getenv('TOKEN')
    OWNER = os.getenv('OWNER')
    bot = SavesBot(int(OWNER) if OWNER is not None else OWNER)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
