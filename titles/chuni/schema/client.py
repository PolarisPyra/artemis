from typing import Optional
from sqlalchemy import Boolean, Column, Integer, String, Table, UniqueConstraint
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row

from artemis.data.schema import metadata
from artemis.data.schema.base import BaseData

bookkeeping: Table = Table(
    "chuni_client_bookkeeping",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(25), nullable=False),
    Column("updateDate", String(25), nullable=False),
    Column("coinCredit", Integer, nullable=False),
    Column("serviceCredit", Integer, nullable=False),
    Column("eMoneyCredit", Integer, nullable=False),
    Column("totalRunningTime", Integer, nullable=False),
    Column("totalPlayTime", Integer, nullable=False),
    Column("averagePlayTime", Integer, nullable=False),
    Column("longestPlayTime", Integer, nullable=False),
    Column("shortestPlayTime", Integer, nullable=False),
    Column("totalCredit", Integer, nullable=False),
    Column("freePlayNum", Integer, nullable=False),
    Column("creditPlayNum", Integer, nullable=False),
    Column("totalPlayNum", Integer, nullable=False),
    Column("firstTutorialNum", Integer, nullable=False),
    Column("masterTutorialNum", Integer, nullable=False),
    Column("playRatio", Integer, nullable=False),
    Column("continueNum", Integer, nullable=False),
    UniqueConstraint("placeId", "clientId", name="chuni_client_bookkeeping_uk"),
    mysql_charset="utf8mb4",
)

develop: Table = Table(
    "chuni_client_develop",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(25), nullable=False),
    Column("orderId", Integer, nullable=False),
    Column("sortNumber", Integer, nullable=False),
    Column("updateDate", String(25), nullable=False),
    Column("devId", Integer, nullable=False),
    Column("devValue", Integer, nullable=False),
    mysql_charset="utf8mb4",
)

error: Table = Table(
    "chuni_client_error",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(25), nullable=False),
    Column("orderId", Integer, nullable=False),
    Column("sortNumber", Integer, nullable=False),
    Column("updateDate", String(25), nullable=False),
    Column("errorNo", Integer, nullable=False),
    Column("totalCount", Integer, nullable=False),
    mysql_charset="utf8mb4",
)

setting: Table = Table(
    "chuni_client_setting",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(25), nullable=False),
    Column("placeName", String(255), nullable=False),
    Column("regionId", Integer, nullable=False),
    Column("regionName", String(255), nullable=False),
    Column("allNetId", Integer, nullable=False),
    Column("bordId", String(25), nullable=False),
    Column("romVersion", String(25), nullable=False),
    Column("dataVersion", String(25), nullable=False),
    Column("dumpFileNum", Integer, nullable=False),
    UniqueConstraint("placeId", "clientId", name="chuni_client_setting_uk"),
    mysql_charset="utf8mb4",
)

testmode: Table = Table(
    "chuni_client_testmode",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(25), nullable=False),
    Column("updateDate", String(25), nullable=False),
    Column("isDelivery", Boolean, nullable=False),
    Column("groupId", Integer, nullable=False),
    Column("groupRole", Integer, nullable=False),
    Column("continueMode", Integer, nullable=False),
    Column("selectMusicTime", Integer, nullable=False),
    Column("advertiseVolume", Integer, nullable=False),
    Column("eventMode", Integer, nullable=False),
    Column("eventMusicNum", Integer, nullable=False),
    Column("machineType", Integer, nullable=False),
    Column("monitorFps", Integer, nullable=False),
    UniqueConstraint("placeId", "clientId", name="chuni_client_testmode_uk"),
    mysql_charset="utf8mb4",
)


class ChuniClientData(BaseData):
    async def put_bookkeeping(self, bookkeeping_data: dict):
        sql = (
            insert(bookkeeping)
            .values(**bookkeeping_data)
            .on_duplicate_key_update(**bookkeeping_data)
        )
        result = await self.execute(sql)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_develop(self, develop_data: dict):
        sql = insert(develop).values(**develop_data)
        result = await self.execute(sql)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_error(self, error_data: dict):
        sql = insert(error).values(**error_data)
        result = await self.execute(sql)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def get_setting(self, place_id: int, client_id: str) -> Optional[Row]:
        sql = setting.select().where(
            (setting.c.placeId == place_id) & (setting.c.clientId == client_id)
        )
        result = await self.execute(sql)

        if result is None:
            return None

        return result.fetchone()

    async def put_setting(self, setting_data: dict):
        sql = (
            insert(setting)
            .values(**setting_data)
            .on_duplicate_key_update(**setting_data)
        )
        result = await self.execute(sql)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_testmode(self, testmode_data: dict):
        sql = (
            insert(testmode)
            .values(**testmode_data)
            .on_duplicate_key_update(**testmode_data)
        )
        result = await self.execute(sql)

        if result is None:
            return None

        return result.inserted_primary_key.id
