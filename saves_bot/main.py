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
    bot = SavesBot()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    bot.run(os.getenv('TOKEN'))


if __name__ == '__main__':
    main()
