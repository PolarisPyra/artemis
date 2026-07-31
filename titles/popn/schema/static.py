from typing import List, Optional

from sqlalchemy import Column, Table, UniqueConstraint, and_, select
from sqlalchemy.engine import Row
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.types import Integer, String

from core.data.schema import BaseData, metadata


music = Table(
    "popn_static_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("songId", Integer),
    Column("chartId", Integer),
    Column("title", String(255)),
    Column("artist", String(255)),
    Column("genre", String(255)),
    Column("category", String(255)),
    Column("difficulty", Integer),
    UniqueConstraint("version", "songId", "chartId", name="popn_static_music_uk"),
    mysql_charset="utf8mb4",
)


class PopnStaticData(BaseData):
    async def put_music(
        self,
        version: int,
        song_id: int,
        chart_id: int,
        title: str,
        artist: str,
        genre: str,
        category: str,
        difficulty: int,
    ) -> Optional[int]:
        sql = insert(music).values(
            version=version,
            songId=song_id,
            chartId=chart_id,
            title=title,
            artist=artist,
            genre=genre,
            category=category,
            difficulty=difficulty,
        )
        conflict = sql.on_duplicate_key_update(
            title=title,
            artist=artist,
            genre=genre,
            category=category,
            difficulty=difficulty,
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_music(
        self, version: int, song_id: Optional[int] = None
    ) -> Optional[List[Row]]:
        sql = select(music).where(music.c.version == version)
        if song_id is not None:
            sql = sql.where(music.c.songId == song_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_music_chart(
        self, version: int, song_id: int, chart_id: int
    ) -> Optional[Row]:
        sql = select(music).where(
            and_(
                music.c.version == version,
                music.c.songId == song_id,
                music.c.chartId == chart_id,
            )
        )
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
