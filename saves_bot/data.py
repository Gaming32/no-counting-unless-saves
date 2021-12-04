import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional, TypedDict, TypeVar

import aiofiles

from saves_bot.utils import WrappingLock

_T = TypeVar('_T')


class UserData(TypedDict):
    saves: float


class GuildData(TypedDict):
    can_count_role: int
    saves: float


class SavesData:
    users_path: Path
    guilds_path: Path
    users: WrappingLock[dict[int, UserData]]
    guilds: WrappingLock[dict[int, GuildData]]
    refreshing_task: Optional[asyncio.Task]

    def __init__(self) -> None:
        self.users_path = Path('users.json')
        self.guilds_path = Path('guilds.json')
        self.users = WrappingLock({})
        self.guilds = WrappingLock({})
        self.last_refresh = 0
        self.refreshing_task = None

    async def refresh_data(self) -> None:
        aloop = asyncio.get_running_loop()
        if self.refreshing_task is not None:
            return await self.refreshing_task
        self.refreshing_task = aloop.create_task(self._refresh_data(aloop))
        await self.refreshing_task
        self.refreshing_task = None

    async def _refresh_data(self, aloop: asyncio.AbstractEventLoop) -> None:
        logging.info('Syncinc saves data...')
        start = time.perf_counter()
        await asyncio.gather(
            self._refresh_single_data_dict(aloop, self.users_path, self.users),
            self._refresh_single_data_dict(aloop, self.guilds_path, self.guilds),
        )
        end = time.perf_counter()
        logging.info('Saves data synced in %f seconds', end - start)

    async def _refresh_single_data_dict(self,
            aloop: asyncio.AbstractEventLoop,
            data_path: Path,
            data_dict: WrappingLock[dict[int, _T]]
        ) -> Optional[_T]:
        try:
            async with aiofiles.open(data_path) as fp:
                datas_str = await fp.read()
        except FileNotFoundError:
            file_datas = {}
        else:
            file_datas: dict[str, _T] = await aloop.run_in_executor(None, json.loads, datas_str)
        async with data_dict as local_datas:
            for (id, data) in file_datas.items():
                id = int(id)
                if id not in local_datas:
                    local_datas[id] = data
            for (id, data) in local_datas.items():
                file_datas[str(id)] = data
        datas_str = await aloop.run_in_executor(None, json.dumps, file_datas)
        async with aiofiles.open(data_path, 'w') as fp:
            await fp.write(datas_str)

    async def get_guild(self, id: int) -> GuildData:
        """Assumes that self.guilds is already locked"""
        try:
            guild_data = self.guilds.value[id]
        except KeyError:
            guild_data: GuildData = {
                'can_count_role': 0,
                'saves': 0,
            }
            self.guilds.value[id] = guild_data
        return guild_data

    async def get_user(self, id: int) -> UserData:
        """Assumes that self.users is already locked"""
        try:
            user_data = self.users.value[id]
        except KeyError:
            user_data: UserData = {
                'saves': 0,
            }
            self.users.value[id] = user_data
        return user_data
