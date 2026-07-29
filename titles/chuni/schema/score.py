from typing import Dict, List, Optional

from sqlalchemy import Column, Table, UniqueConstraint, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.types import Boolean, Integer, String

from core.data.schema import BaseData, metadata

from ..config import ChuniConfig

course: Table = Table(
    "chuni_score_course",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("courseId", Integer),
    Column("classId", Integer),
    Column("playCount", Integer),
    Column("scoreMax", Integer),
    Column("isFullCombo", Boolean),
    Column("isAllJustice", Boolean),
    Column("isSuccess", Integer),
    Column("scoreRank", Integer),
    Column("eventId", Integer),
    Column("lastPlayDate", String(25)),
    Column("param1", Integer),
    Column("param2", Integer),
    Column("param3", Integer),
    Column("param4", Integer),
    Column("isClear", Integer),
    Column("theoryCount", Integer),
    Column("orderId", Integer),
    Column("playerRating", Integer),
    UniqueConstraint("user", "courseId", name="chuni_score_course_uk"),
    mysql_charset="utf8mb4",
)

best_score: Table = Table(
    "chuni_score_best",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("playCount", Integer),
    Column("scoreMax", Integer),
    Column("resRequestCount", Integer),
    Column("resAcceptCount", Integer),
    Column("resSuccessCount", Integer),
    Column("missCount", Integer),
    Column("maxComboCount", Integer),
    Column("isFullCombo", Boolean),
    Column("isAllJustice", Boolean),
    Column("isSuccess", Integer),
    Column("fullChain", Integer),
    Column("maxChain", Integer),
    Column("scoreRank", Integer),
    Column("isLock", Boolean),
    Column("ext1", Integer),
    Column("theoryCount", Integer),
    UniqueConstraint("user", "musicId", "level", name="chuni_score_best_uk"),
    mysql_charset="utf8mb4",
)

playlog = Table(
    "chuni_score_playlog",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("orderId", Integer),
    Column("sortNumber", Integer),
    Column("placeId", Integer),
    Column("playDate", String(20)),
    Column("userPlayDate", String(20)),
    Column("musicId", Integer),
    Column("level", Integer),
    Column("customId", Integer),
    Column("playedUserId1", Integer),
    Column("playedUserId2", Integer),
    Column("playedUserId3", Integer),
    Column("playedUserName1", String(20)),
    Column("playedUserName2", String(20)),
    Column("playedUserName3", String(20)),
    Column("playedMusicLevel1", Integer),
    Column("playedMusicLevel2", Integer),
    Column("playedMusicLevel3", Integer),
    Column("playedCustom1", Integer),
    Column("playedCustom2", Integer),
    Column("playedCustom3", Integer),
    Column("track", Integer),
    Column("score", Integer),
    Column("rank", Integer),
    Column("maxCombo", Integer),
    Column("maxChain", Integer),
    Column("rateTap", Integer),
    Column("rateHold", Integer),
    Column("rateSlide", Integer),
    Column("rateAir", Integer),
    Column("rateFlick", Integer),
    Column("judgeGuilty", Integer),
    Column("judgeAttack", Integer),
    Column("judgeJustice", Integer),
    Column("judgeCritical", Integer),
    Column("eventId", Integer),
    Column("playerRating", Integer),
    Column("isNewRecord", Boolean),
    Column("isFullCombo", Boolean),
    Column("fullChainKind", Integer),
    Column("isAllJustice", Boolean),
    Column("isContinue", Boolean),
    Column("isFreeToPlay", Boolean),
    Column("characterId", Integer),
    Column("skillId", Integer),
    Column("playKind", Integer),
    Column("isClear", Integer),
    Column("skillLevel", Integer),
    Column("skillEffect", Integer),
    Column("placeName", String(255)),
    Column("isMaimai", Boolean),
    Column("commonId", Integer),
    Column("charaIllustId", Integer),
    Column("romVersion", String(255)),
    Column("judgeHeaven", Integer),
    Column("regionId", Integer),
    Column("machineType", Integer),
    Column("ticketId", Integer),
    Column("monthPoint", Integer, default=None, server_default=text("NULL")),
    Column("eventPoint", Integer, default=None, server_default=text("NULL")),
    mysql_charset="utf8mb4",
)


class ChuniScoreData(BaseData):
    async def get_courses(
        self,
        aime_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        sql = select(course).where(course.c.user == aime_id)

        if limit is not None or offset is not None:
            sql = sql.order_by(course.c.id)
        if limit is not None:
            sql = sql.limit(limit)
        if offset is not None:
            sql = sql.offset(offset)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_course(self, aime_id: int, course_data: Dict) -> Optional[int]:
        course_data["user"] = aime_id
        course_data = self.fix_bools(course_data)

        sql = insert(course).values(**course_data)
        conflict = sql.on_duplicate_key_update(**course_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_scores(
        self,
        aime_id: int,
        levels: Optional[list[int]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Optional[List[Row]]:
        condition = best_score.c.user == aime_id

        if levels is not None:
            condition &= best_score.c.level.in_(levels)

        if limit is None and offset is None:
            sql = (
                select(best_score)
                .where(condition)
                .order_by(best_score.c.musicId.asc(), best_score.c.level.asc())
            )
        else:
            subq = (
                select(best_score.c.musicId)
                .distinct()
                .where(condition)
                .order_by(best_score.c.musicId)
            )

            if limit is not None:
                subq = subq.limit(limit)
            if offset is not None:
                subq = subq.offset(offset)

            subq = subq.subquery()

            sql = (
                select(best_score)
                .join(subq, best_score.c.musicId == subq.c.musicId)
                .where(condition)
                .order_by(best_score.c.musicId, best_score.c.level)
            )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_score(self, aime_id: int, score_data: Dict) -> Optional[int]:
        score_data["user"] = aime_id
        score_data = self.fix_bools(score_data)

        sql = insert(best_score).values(**score_data)
        conflict = sql.on_duplicate_key_update(**score_data)

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_playlogs(self, aime_id: int) -> Optional[Row]:
        sql = select(playlog).where(playlog.c.user == aime_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_playlogs_limited(
        self, aime_id: int, index: int, count: int
    ) -> Optional[Row]:
        sql = (
            select(playlog)
            .where(playlog.c.user == aime_id)
            .order_by(playlog.c.id.desc())
            .limit(count)
            .offset(index * count)
        )

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f" aime_id {aime_id} has no playlog ")
            return None
        return result.fetchall()

    async def get_user_playlogs_count(self, aime_id: int) -> Optional[Row]:
        sql = select(func.count()).where(playlog.c.user == aime_id)
        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f" aime_id {aime_id} has no playlog ")
            return None
        return result.scalar()

    async def put_playlog(
        self, aime_id: int, playlog_data: Dict, version: int
    ) -> Optional[int]:
        # Calculate the ROM version that should be inserted into the DB, based on the version of the ggame being inserted
        # We only need from Version 10 (Plost) and back, as newer versions include romVersion in their upsert
        # This matters both for gameRankings, as well as a future DB update to keep version data separate
        romVer = {
            10: "1.50.0",
            9: "1.45.0",
            8: "1.40.0",
            7: "1.35.0",
            6: "1.30.0",
            5: "1.25.0",
            4: "1.20.0",
            3: "1.15.0",
            2: "1.10.0",
            1: "1.05.0",
            0: "1.00.0",
        }

        playlog_data["user"] = aime_id
        playlog_data = self.fix_bools(playlog_data)
        if "romVersion" not in playlog_data:
            playlog_data["romVersion"] = romVer.get(version, "1.00.0")

        sql = insert(playlog).values(**playlog_data)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def get_rankings(self, version: int) -> Optional[List[Dict]]:
        # Calculates the ROM version that should be fetched for rankings, based on the game version being retrieved
        # This prevents tracks that are not accessible in your version from counting towards the 10 results
        romVer = {
            15: "2.20%",
            14: "2.15%",
            13: "2.10%",
            12: "2.05%",
            11: "2.00%",
            10: "1.50%",
            9: "1.45%",
            8: "1.40%",
            7: "1.35%",
            6: "1.30%",
            5: "1.25%",
            4: "1.20%",
            3: "1.15%",
            2: "1.10%",
            1: "1.05%",
            0: "1.00%",
        }
        sql = (
            select(
                [
                    playlog.c.musicId.label("id"),
                    func.count(playlog.c.musicId).label("point"),
                ]
            )
            .where(
                (playlog.c.level != 4)
                & (playlog.c.romVersion.like(romVer.get(version, "%")))
            )
            .group_by(playlog.c.musicId)
            .order_by(func.count(playlog.c.musicId).desc())
            .limit(10)
        )
        result = await self.execute(sql)

        if result is None:
            return None

        rows = result.fetchall()
        return [dict(row) for row in rows]
