from typing import Any, Dict, List, Optional

from sqlalchemy import BigInteger, Column, Table, select
from sqlalchemy.engine import Row
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import Boolean, DateTime, Integer, String

from core.data.schema import BaseData, metadata


playlog = Table(
    "popn_playlog",
    metadata,
    Column("id", BigInteger, primary_key=True, nullable=False),
    Column(
        "user_id",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("ref_id", String(32)),
    Column("data_id", String(32)),
    Column("name", String(32)),
    Column("chara_num", Integer),
    Column("mode", Integer),
    Column("play_id", Integer),
    Column("stage", Integer),
    Column("music_num", Integer),
    Column("sheet_num", Integer),
    Column("clear_type", Integer),
    Column("clear_rank", Integer),
    Column("score", Integer),
    Column("cool", Integer),
    Column("great", Integer),
    Column("good", Integer),
    Column("bad", Integer),
    Column("combo", Integer),
    Column("highlight", Integer),
    Column("gauge", Integer),
    Column("gauge_type", Integer),
    Column("is_netvs", Integer),
    Column("is_win", Integer),
    Column("is_image_store", Boolean),
    Column("is_option_save", Boolean),
    Column("hispeed", Integer),
    Column("popkun", Integer),
    Column("hidden", Boolean),
    Column("hidden_rate", Integer),
    Column("sudden", Boolean),
    Column("sudden_rate", Integer),
    Column("randmir", Integer),
    Column("ojama_0", Integer),
    Column("ojama_1", Integer),
    Column("forever_0", Boolean),
    Column("forever_1", Boolean),
    Column("full_setting", Boolean),
    Column("guide_se", Integer),
    Column("guide_se_vol", Integer),
    Column("lift", Boolean),
    Column("lift_rate", Integer),
    Column("judge_ad", Integer),
    Column("roof", Integer),
    Column("long_pop", Integer),
    Column("judge", Integer),
    Column("slow", Integer),
    Column("fast", Integer),
    Column("ex_gauge_lv", Integer),
    Column("is_super_extra", Integer),
    Column("netvs_ojama_type", Integer),
    Column("netvs_type", Integer),
    Column("netvs_rank", Integer),
    Column("netvs_ojama_0", Integer),
    Column("netvs_ojama_1", Integer),
    Column("netvs_ojama_2", Integer),
    Column("play_date", BigInteger),
    Column("select_total_time", Integer),
    Column("select_used_time", Integer),
    Column("select_remain_time", Integer),
    Column("category", Integer),
    Column("sub_category", Integer),
    Column("matching", Integer),
    Column("ojama_vs", Integer),
    Column("playdate", DateTime, server_default=func.now()),
    mysql_charset="utf8mb4",
)


class PopnScoreData(BaseData):
    async def put_playlog(self, user_id: int, values: Dict[str, Any]) -> Optional[int]:
        values = dict(values)
        values["user_id"] = user_id
        values = {
            key: value for key, value in values.items() if key in playlog.c
        }
        values = self.fix_bools(values)

        result = await self.execute(playlog.insert().values(**values))
        if result is None:
            self.logger.error("Failed to insert Pop'n playlog for user %s", user_id)
            return None
        return result.lastrowid

    async def get_playlogs(self, user_id: int) -> Optional[List[Row]]:
        result = await self.execute(
            select(playlog)
            .where(playlog.c.user_id == user_id)
            .order_by(playlog.c.id)
        )
        return None if result is None else result.fetchall()

    async def get_scores(self, user_id: int) -> List[Dict[str, Any]]:
        rows = await self.get_playlogs(user_id)
        if not rows:
            return []

        latest: Dict[tuple, Row] = {}
        counts: Dict[tuple, int] = {}
        for row in rows:
            music_num = row._mapping.get("music_num")
            sheet_num = row._mapping.get("sheet_num")
            if music_num is None or sheet_num is None:
                continue
            key = (music_num, sheet_num)
            counts[key] = counts.get(key, 0) + 1
            latest[key] = row

        output: List[Dict[str, Any]] = []
        for key, row in latest.items():
            mapping = dict(row._mapping)
            mapping["cnt"] = counts[key]
            output.append(mapping)
        return output
