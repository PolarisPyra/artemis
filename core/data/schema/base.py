import asyncio
import json
import logging
from random import randrange
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy import Column, MetaData, Table, UniqueConstraint
from sqlalchemy.engine import Row
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, text, and_, or_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.types import INTEGER, JSON, TEXT, TIMESTAMP, Integer, String

from core.config import CoreConfig

metadata = MetaData()

event_log: Table = Table(
    "event_log",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("system", String(255), nullable=False),
    Column("type", String(255), nullable=False),
    Column("severity", Integer, nullable=False),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade")),
    Column("arcade", INTEGER, ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade")),
    Column("machine", INTEGER, ForeignKey("machine.id", ondelete="cascade", onupdate="cascade")),
    Column("ip", TEXT(39)),
    Column("game", TEXT(4)),
    Column("version", TEXT(24)),
    Column("message", String(1000), nullable=False),
    Column("details", JSON, nullable=False),
    Column("when_logged", TIMESTAMP, nullable=False, server_default=func.now()),
    mysql_charset="utf8mb4",
)

campaign: Table = Table(
    "campaign",
    metadata,
    Column("id", INTEGER, primary_key=True, nullable=False),
    Column("name", String(127), nullable=False),
    Column("announce_date", TIMESTAMP), # None = start announcing now
    Column("start_date", TIMESTAMP), # None = start now
    Column("end_date", TIMESTAMP), # None = never end
    Column("distrib_start_date", TIMESTAMP), # None = start distributing now
    Column("distrib_end_date", TIMESTAMP), # None = never stop distributing
    # These are for legacy campaign requests prior to ADB v3.03.0.
    Column("info0", INTEGER),
    Column("info1", INTEGER),
    Column("info2", INTEGER),
    Column("info3", INTEGER),
    mysql_charset="utf8mb4",
)

# Unfortunatly without a machine table change there's no real way to gate by game version...
campaign_game: Table = Table(
    "campaign_game",
    metadata,
    Column("campaign_id", INTEGER, ForeignKey("campaign.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("game_id", String(5), nullable=False),
    UniqueConstraint("campaign_id", "game_id", name="campaign_game_uk"),
    mysql_charset="utf8mb4",
)

class BaseData:
    def __init__(self, cfg: CoreConfig, conn: "sessionmaker[AsyncSession]") -> None:
        self.config = cfg
        self.conn = conn
        self.logger = logging.getLogger("database")

    async def execute(self, sql: str, opts: Dict[str, Any] = {}) -> Optional[CursorResult]:
        res = None

        async with self.conn() as session:
            try:
                self.logger.debug(f"SQL Execute: {''.join(str(sql).splitlines())}")
                res = await session.execute(text(sql), opts)

            except SQLAlchemyError as e:
                self.logger.error(f"SQLAlchemy error {e}")
                return None

            except UnicodeEncodeError as e:
                self.logger.error(f"UnicodeEncodeError error {e}")
                return None

            except Exception:
                try:
                    res = await session.execute(sql, opts)

                except SQLAlchemyError as e:
                    self.logger.error(f"SQLAlchemy error {e}")
                    return None

                except UnicodeEncodeError as e:
                    self.logger.error(f"UnicodeEncodeError error {e}")
                    return None

                except Exception:
                    self.logger.error(f"Unknown error")
                    raise

        return res

    def generate_id(self) -> int:
        """
        Generate a random 5-7 digit id
        """
        return randrange(10000, 9999999)

    async def log_event(
        self, system: str, type: str, severity: int, message: str, details: Dict = {}, user: int = None, 
        arcade: int = None, machine: int = None, ip: Optional[str] = None, game: Optional[str] = None, version: Optional[str] = None
    ) -> Optional[int]:
        sql = event_log.insert().values(
            system=system,
            type=type,
            severity=severity,
            user=user,
            arcade=arcade,
            machine=machine,
            ip=ip,
            game=game,
            version=version,
            message=message,
            details=json.dumps(details),
        )
        result = await self.execute(sql)

        if result is None:
            self.logger.error(
                f"{__name__}: Failed to insert event into event log! system = {system}, type = {type}, severity = {severity}, message = {message}"
            )
            return None

        return result.lastrowid

    async def get_event_log(self, entries: int = 100) -> Optional[List[Row]]:
        sql = event_log.select().order_by(event_log.c.id.desc()).limit(entries)
        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def create_campaign(self, campaign_id: int, name: str, announce_date: Optional[datetime] = None, 
                              start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                              distribute_start_date: Optional[datetime] = None, distribute_end_date: Optional[datetime] = None) -> Optional[int]:
        sql = insert(campaign).values(
            id = campaign_id,
            name = name,
            announce_date = announce_date,
            start_date = start_date,
            end_date = end_date,
            distribute_start_date = distribute_start_date,
            distribute_end_date = distribute_end_date,
        )

        conflict = sql.on_duplicate_key_update(
            announce_date = announce_date,
            start_date = start_date,
            end_date = end_date,
            distribute_start_date = distribute_start_date,
            distribute_end_date = distribute_end_date,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to create campaign {name} ID {campaign_id}!")
            return None
        return result.lastrowid

    async def create_campaign_old(self, campaign_id: int, info0: int = 0, info1: int = 0, info2: int = 0, info3: int = 0) -> Optional[int]:
        sql = insert(campaign).values(
            id = campaign_id,
            info0 = info0,
            info1 = info1,
            info2 = info2,
            info3 = info3
        )

        conflict = sql.on_duplicate_key_update(
            info0 = info0,
            info1 = info1,
            info2 = info2,
            info3 = info3
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to create legacy campaign with ID {campaign_id}!")
            return None
        return result.lastrowid

    async def add_game_to_campaign(self, campaign_id: int, game_id: str) -> bool:
        sql = insert(campaign_game).values(
            id = campaign_id,
            game_id = game_id
        )

        conflict = sql.on_duplicate_key_do_nothing()

        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to add game {game_id} to campaign {campaign_id}!")
            return False
        return True

    async def get_campaigns_by_game(self, game_id: str) -> Optional[List[Row]]:
        result = await self.execute(campaign
            .join(campaign_game, campaign.c.id == campaign_game.c.campaign_id)
            .select(campaign_game.c.game_id == game_id))
        
        if result is not None:
            return result.fetchall()

    async def get_active_campaigns_by_game(self, game_id: str) -> Optional[List[Row]]:
        result = await self.execute(campaign
            .join(campaign_game, campaign.c.id == campaign_game.c.campaign_id)
            .select(and_(campaign_game.c.game_id == game_id, and_(
                # TODO: Maybe add a RANK statement to prioritize campaigns that have set end dates?
                or_(campaign.c.announce_date >= datetime.now(), campaign.c.announce_date == None),
                or_(campaign.c.distrib_end_date < datetime.now(), campaign.c.distrib_end_date == None),
            ))))
        
        if result is not None:
            return result.fetchall()

    async def get_campaigns(self) -> Optional[List[Row]]:
        result = await self.execute(campaign.select())

        if result is not None:
            return result.fetchall()

    async def get_active_campaigns(self) -> Optional[List[Row]]:
        result = await self.execute(campaign
            .select(and_(
                or_(campaign.c.announce_date >= datetime.now(), campaign.c.announce_date == None),
                or_(campaign.c.distrib_end_date < datetime.now(), campaign.c.distrib_end_date == None),
            )))
        
        if result is not None:
            return result.fetchall()

    async def get_campaign_by_id(self, campaign_id: int) -> Optional[Row]:
        result = await self.execute(campaign.select(campaign.c.id == campaign_id))

        if result is not None:
            return result.fetchone()

    async def get_games_in_campaign(self, campaign_id: int) -> Optional[List[Row]]:
        result = await self.execute(campaign_game.select(campaign_game.c.campaign_id == campaign_id))

        if result is not None:
            return result.fetchall()

    async def is_game_in_campaign(self, game_id: str, campaign_id: int) -> bool:
        result = await self.execute(campaign_game.select(and_(
            campaign_game.c.campaign_id == campaign_id,
            campaign_game.c.game_id == game_id
        )))
        
        if result is not None:
            return result.fetchone() is not None
        return False

    def fix_bools(self, data: Dict) -> Dict:
        for k, v in data.items():
            if k == "userName" or k == "teamName":
                continue
            if type(v) == str and v.lower() == "true":
                data[k] = True
            elif type(v) == str and v.lower() == "false":
                data[k] = False

        return data
