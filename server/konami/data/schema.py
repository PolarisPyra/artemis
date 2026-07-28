"""Konami/e-amusement database schema.

The table layout intentionally follows the MySQL schema used by bemaniutils.
The Konami metadata is separate from Artemis' Aime, arcade, and system metadata.
``konami_document`` remains as a compatibility store for routes that have not
yet been moved to the normalized tables.
"""

import hashlib
import time
from typing import Optional

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT as MySQLBigInteger
from sqlalchemy.types import JSON

from server.sega.data.schema.base import BaseData

konami_metadata = MetaData()


def _table(name: str, *columns, **kwargs) -> Table:
    return Table(name, konami_metadata, *columns, mysql_charset="utf8mb4", **kwargs)


bigint = MySQLBigInteger(unsigned=True)

session = _table(
    "session",
    Column("id", Integer, nullable=False),
    Column("type", String(32), nullable=False),
    Column("session", String(32), nullable=False, unique=True),
    Column("expiration", Integer),
)

user = _table(
    "user",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("pin", String(4), nullable=False),
    Column("username", String(255), unique=True),
    Column("password", String(255)),
    Column("email", String(255)),
    Column("admin", Integer),
)

card = _table(
    "card",
    Column("id", String(16), nullable=False, unique=True),
    Column("userid", bigint, nullable=False, index=True),
)

extid = _table(
    "extid",
    Column("game", String(32), nullable=False),
    Column("extid", Integer, nullable=False, unique=True),
    Column("userid", bigint, nullable=False),
    UniqueConstraint("game", "userid", name="game_userid"),
)

refid = _table(
    "refid",
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("refid", String(16), nullable=False, unique=True),
    Column("userid", bigint, nullable=False),
    UniqueConstraint("game", "version", "userid", name="game_version_userid"),
)

profile = _table(
    "profile",
    Column("refid", String(16), nullable=False, unique=True),
    Column("data", JSON, nullable=False),
)

achievement = _table(
    "achievement",
    Column("refid", String(16), nullable=False),
    Column("id", Integer, nullable=False),
    Column("type", String(64), nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("refid", "id", "type", name="refid_id_type"),
)

time_based_achievement = _table(
    "time_based_achievement",
    Column("refid", String(16), nullable=False),
    Column("id", Integer, nullable=False),
    Column("type", String(64), nullable=False),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("data", JSON, nullable=False),
    UniqueConstraint("refid", "id", "type", "timestamp", name="refid_id_type_timestamp"),
)

balance = _table(
    "balance",
    Column("userid", bigint, nullable=False),
    Column("arcadeid", Integer, nullable=False),
    Column("balance", Integer, nullable=False),
    UniqueConstraint("userid", "arcadeid", name="userid_arcadeid"),
)

link = _table(
    "link",
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("userid", bigint, nullable=False),
    Column("type", String(64), nullable=False),
    Column("other_userid", bigint, nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "version", "userid", "type", "other_userid", name="game_version_userid_type_other_userid"),
)

score = _table(
    "score",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("userid", bigint, nullable=False),
    Column("musicid", Integer, nullable=False, index=True),
    Column("points", Integer, nullable=False, index=True),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("update", Integer, nullable=False, index=True),
    Column("lid", Integer, nullable=False, index=True),
    Column("data", JSON, nullable=False),
    UniqueConstraint("userid", "musicid", name="userid_musicid"),
)

score_history = _table(
    "score_history",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("userid", bigint, nullable=False),
    Column("musicid", Integer, nullable=False, index=True),
    Column("points", Integer, nullable=False),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("lid", Integer, nullable=False, index=True),
    Column("new_record", Integer, nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("userid", "musicid", "timestamp", name="userid_musicid_timestamp"),
)

music = _table(
    "music",
    Column("id", Integer, nullable=False, index=True),
    Column("songid", Integer, nullable=False),
    Column("chart", Integer, nullable=False),
    Column("game", String(32), nullable=False, index=True),
    Column("version", Integer, nullable=False, index=True),
    Column("name", String(255)),
    Column("artist", String(255)),
    Column("genre", String(255)),
    Column("data", JSON),
    UniqueConstraint("songid", "chart", "game", "version", name="songid_chart_game_version"),
)

game_settings = _table(
    "game_settings",
    Column("game", String(32), nullable=False),
    Column("userid", bigint, nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "userid", name="game_userid_settings"),
)

catalog = _table(
    "catalog",
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("id", Integer, nullable=False),
    Column("type", String(64), nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "version", "id", "type", name="game_version_id_type"),
)

series_achievement = _table(
    "series_achievement",
    Column("game", String(32), nullable=False),
    Column("userid", bigint, nullable=False),
    Column("id", Integer, nullable=False),
    Column("type", String(64), nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "userid", "id", "type", name="game_userid_id_type"),
)

time_sensitive_settings = _table(
    "time_sensitive_settings",
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("name", String(32), nullable=False),
    Column("start_time", Integer, nullable=False, index=True),
    Column("end_time", Integer, nullable=False, index=True),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "version", "name", "start_time", name="game_version_name_start_time"),
)

machine = _table(
    "machine",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("pcbid", String(20), nullable=False, unique=True),
    Column("name", String(255), nullable=False),
    Column("description", String(255), nullable=False),
    Column("arcadeid", Integer),
    Column("port", Integer, nullable=False, unique=True),
    Column("game", String(20)),
    Column("version", Integer),
    Column("data", JSON),
)

arcade = _table(
    "arcade",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", String(255), nullable=False),
    Column("pin", String(8), nullable=False),
    Column("pref", Integer, nullable=False),
    Column("area", String(63)),
    Column("data", JSON),
)

arcade_owner = _table(
    "arcade_owner",
    Column("userid", bigint, nullable=False),
    Column("arcadeid", Integer, nullable=False),
    UniqueConstraint("userid", "arcadeid", name="userid_arcadeid_owner"),
)

arcade_settings = _table(
    "arcade_settings",
    Column("arcadeid", Integer, nullable=False),
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("type", String(64), nullable=False),
    Column("data", JSON, nullable=False),
    UniqueConstraint("arcadeid", "game", "version", "type", name="arcadeid_game_version_type"),
)

news = _table(
    "news",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("title", String(255), nullable=False),
    Column("body", Text, nullable=False),
)

scheduled_work = _table(
    "scheduled_work",
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("name", String(32), nullable=False),
    Column("schedule", String(32), nullable=False),
    Column("year", Integer),
    Column("day", Integer),
    UniqueConstraint("game", "version", "name", "schedule", name="game_version_name_schedule"),
)

audit = _table(
    "audit",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("userid", bigint, index=True),
    Column("arcadeid", Integer, index=True),
    Column("type", String(64), nullable=False, index=True),
    Column("data", JSON, nullable=False),
)

playsession = _table(
    "playsession",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("userid", bigint, nullable=False),
    Column("time", Integer, nullable=False, index=True),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "version", "userid", name="game_version_userid_playsession"),
)

lobby = _table(
    "lobby",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("game", String(32), nullable=False),
    Column("version", Integer, nullable=False),
    Column("userid", bigint, nullable=False),
    Column("time", Integer, nullable=False, index=True),
    Column("data", JSON, nullable=False),
    UniqueConstraint("game", "version", "userid", name="game_version_userid_lobby"),
)

client = _table(
    "client",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("token", String(36), nullable=False),
)

server = _table(
    "server",
    Column("id", Integer, nullable=False, primary_key=True),
    Column("timestamp", Integer, nullable=False, index=True),
    Column("uri", String(1024), nullable=False),
    Column("token", String(64), nullable=False),
    Column("config", Integer, nullable=False),
)

konami_document = _table(
    "konami_document",
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("refid", String(32), nullable=False),
    Column("game_code", String(8), nullable=False),
    Column("collection", String(64), nullable=False),
    Column("version", String(32), nullable=False, default=""),
    Column("document", JSON, nullable=False),
    UniqueConstraint("refid", "game_code", "collection", "version", name="konami_document_uk"),
)


class KonamiData(BaseData):
    """Persistence helpers for the normalized e-amusement tables.

    The public methods use the shape expected by the Pop'n handlers while the
    storage follows the corresponding bemaniutils concepts: one profile per
    refid, one score per user/music mapping, and keyed achievement records.
    """

    GAME = "popnmusic"

    @staticmethod
    def _version_number(version: str) -> int:
        try:
            return int(version.removeprefix("v"))
        except (AttributeError, ValueError):
            return 0

    @staticmethod
    def _stable_id(value: str) -> int:
        # Keep IDs positive and within a signed 32-bit integer. The collision
        # check in _userid/_musicid handles the exceptionally unlikely clash.
        return int(hashlib.sha256(value.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF

    async def _userid(
        self, refid_value: str, game: str = GAME, version: int = 0, create: bool = True
    ) -> Optional[int]:
        result = await self.execute(
            refid.select().where(
                (refid.c.game == game)
                & (refid.c.version == version)
                & (refid.c.refid == refid_value)
            )
        )
        row = result.fetchone() if result is not None else None
        if row is not None:
            return int(row["userid"])
        if not create:
            return None

        userid = self._stable_id(f"user:{refid_value}")
        existing = await self.execute(user.select().where(user.c.id == userid))
        if existing is not None and existing.fetchone() is not None:
            # Resolve a hash collision deterministically without changing the
            # refid's identity on subsequent requests.
            userid = self._stable_id(f"user:{refid_value}:konami")
        await self.execute(
            user.insert().values(
                id=userid,
                pin="0000",
                username=None,
                password=None,
                email=None,
                admin=0,
            )
        )
        await self.execute(
            refid.insert().values(
                game=game,
                version=version,
                refid=refid_value,
                userid=userid,
            )
        )
        return userid

    async def get_profile(self, refid_value: str) -> Optional[dict]:
        result = await self.execute(
            profile.select().where(profile.c.refid == refid_value)
        )
        row = result.fetchone() if result is not None else None
        return row["data"] if row is not None else None

    async def put_profile(self, refid_value: str, data: dict) -> None:
        await self._userid(refid_value)
        from sqlalchemy.dialects.mysql import insert

        statement = insert(profile).values(refid=refid_value, data=data)
        await self.execute(statement.on_duplicate_key_update(data=data))

    async def put_card(self, card_id: str, refid_value: str) -> None:
        userid = await self._userid(refid_value)
        from sqlalchemy.dialects.mysql import insert

        statement = insert(card).values(id=card_id, userid=userid)
        await self.execute(statement.on_duplicate_key_update(userid=userid))

    async def put_extid(self, refid_value: str, game: str, extid_value: int) -> None:
        userid = await self._userid(refid_value)
        from sqlalchemy.dialects.mysql import insert

        values = {"game": game, "extid": extid_value, "userid": userid}
        statement = insert(extid).values(**values)
        await self.execute(statement.on_duplicate_key_update(userid=userid))

    async def get_achievement_document(
        self, refid_value: str, game: str, version: str
    ) -> Optional[dict]:
        result = await self.execute(
            achievement.select().where(
                (achievement.c.refid == refid_value)
                & (achievement.c.id == self._version_number(version))
                & (achievement.c.type == game)
            )
        )
        row = result.fetchone() if result is not None else None
        return row["data"] if row is not None else None

    async def put_achievement_document(
        self, refid_value: str, game: str, version: str, data: dict
    ) -> None:
        await self._userid(refid_value)
        from sqlalchemy.dialects.mysql import insert

        values = {
            "refid": refid_value,
            "id": self._version_number(version),
            "type": game,
            "data": data,
        }
        statement = insert(achievement).values(**values)
        await self.execute(statement.on_duplicate_key_update(data=data))

    async def _musicid(self, songid: int, chart: int, version: int) -> int:
        result = await self.execute(
            music.select().where(
                (music.c.songid == songid)
                & (music.c.chart == chart)
                & (music.c.game == self.GAME)
                & (music.c.version == version)
            )
        )
        row = result.fetchone() if result is not None else None
        if row is not None:
            return int(row["id"])

        musicid = self._stable_id(f"music:{self.GAME}:{version}:{songid}:{chart}")
        await self.execute(
            music.insert().values(
                id=musicid,
                songid=songid,
                chart=chart,
                game=self.GAME,
                version=version,
                data={},
            )
        )
        return musicid

    async def get_scores(self, refid_value: str, version: str) -> dict:
        userid = await self._userid(refid_value, create=False)
        if userid is None:
            return {"collection": "scores", "version": version, "scores": {}}

        version_number = self._version_number(version)
        result = await self.execute(
            score.select()
            .select_from(score.join(music, score.c.musicid == music.c.id))
            .where(
                (score.c.userid == userid)
                & (music.c.game == self.GAME)
                & (music.c.version == version_number)
            )
        )
        scores = {}
        if result is not None:
            for row in result.fetchall():
                music_row = row._mapping
                mapping = await self.execute(
                    music.select().where(music.c.id == music_row["musicid"])
                )
                song = mapping.fetchone() if mapping is not None else None
                if song is None:
                    continue
                scores[f'{song["songid"]}:{song["chart"]}'] = {
                    "score": int(music_row["points"]),
                    "clear_type": int(
                        (music_row["data"] or {}).get(
                            "clear_type", (music_row["data"] or {}).get("clear", 0)
                        )
                    ),
                    "cnt": int((music_row["data"] or {}).get("cnt", 0)),
                }
        return {"collection": "scores", "version": version, "scores": scores}

    async def put_scores(self, refid_value: str, version: str, document: dict) -> None:
        version_number = self._version_number(version)
        userid = await self._userid(refid_value)
        for songid_value, styles in document.get("scores", {}).items():
            flat_score = ":" in str(songid_value) and isinstance(styles, dict) and "score" in styles
            if flat_score:
                try:
                    songid, style = (int(value) for value in str(songid_value).split(":", 1))
                except ValueError:
                    continue
                levels = {str(style): {"0": styles}}
            else:
                try:
                    songid = int(songid_value)
                except (TypeError, ValueError):
                    continue
                levels = styles
            if not isinstance(levels, dict):
                continue
            for style_value, level_values in levels.items():
                try:
                    if ":" not in str(songid_value) or not isinstance(styles, dict) or "score" not in styles:
                        style = int(style_value)
                except (TypeError, ValueError):
                    continue
                for level_value, value in level_values.items():
                    try:
                        level = int(level_value) if ":" not in str(songid_value) else 0
                        points = int(value.get("score", 0))
                    except (AttributeError, TypeError, ValueError):
                        continue
                    chart = style if flat_score else style * 1000 + level
                    musicid = await self._musicid(songid, chart, version_number)
                    now = int(time.time())
                    score_data = {
                        "clear_type": int(value.get("clear_type", value.get("clear", 0))),
                        "cnt": int(value.get("cnt", 0)),
                    }
                    from sqlalchemy.dialects.mysql import insert

                    values = {
                        "userid": userid,
                        "musicid": musicid,
                        "points": points,
                        "timestamp": now,
                        "update": now,
                        "lid": 0,
                        "data": score_data,
                    }
                    statement = insert(score).values(**values)
                    await self.execute(
                        statement.on_duplicate_key_update(
                            points=func.greatest(score.c.points, points),
                            update=now,
                            data=score_data,
                        )
                    )
                    history_values = {
                        "userid": userid,
                        "musicid": musicid,
                        "points": points,
                        "timestamp": now,
                        "lid": 0,
                        "new_record": 1,
                        "data": score_data,
                    }
                    await self.execute(score_history.insert().values(**history_values))

    async def get_rivals(self, refid_value: str) -> list[str]:
        userid = await self._userid(refid_value, create=False)
        if userid is None:
            return []
        result = await self.execute(
            link.select().where(
                (link.c.game == self.GAME)
                & (link.c.version == 0)
                & (link.c.userid == userid)
                & (link.c.type == "rival")
            )
        )
        if result is None:
            return []
        return [
            str((row["data"] or {}).get("refid"))
            for row in result.fetchall()
            if (row["data"] or {}).get("refid")
        ]

    async def put_rivals(self, refid_value: str, rival_ids: list[str]) -> None:
        userid = await self._userid(refid_value)
        await self.execute(
            link.delete().where(
                (link.c.game == self.GAME)
                & (link.c.version == 0)
                & (link.c.userid == userid)
                & (link.c.type == "rival")
            )
        )
        from sqlalchemy.dialects.mysql import insert

        for rival_id in rival_ids:
            other_userid = await self._userid(rival_id)
            values = {
                "game": self.GAME,
                "version": 0,
                "userid": userid,
                "type": "rival",
                "other_userid": other_userid,
                "data": {"refid": rival_id},
            }
            await self.execute(insert(link).values(**values))

    async def get_document(
        self, refid: str, game_code: str, collection: str, version: str = ""
    ):
        result = await self.execute(
            konami_document.select().where(
                (konami_document.c.refid == refid)
                & (konami_document.c.game_code == game_code)
                & (konami_document.c.collection == collection)
                & (konami_document.c.version == version)
            )
        )
        row = result.fetchone() if result is not None else None
        return row["document"] if row is not None else None

    async def put_document(
        self,
        refid: str,
        game_code: str,
        collection: str,
        document: dict,
        version: str = "",
    ):
        from sqlalchemy.dialects.mysql import insert

        statement = insert(konami_document).values(
            refid=refid,
            game_code=game_code,
            collection=collection,
            version=version,
            document=document,
        )
        return await self.execute(statement.on_duplicate_key_update(document=document))

    async def documents(
        self,
        game_code: str,
        collection: str,
        version: str = "",
        refid: str = "",
    ) -> list[tuple[str, dict]]:
        if collection == "profile":
            conditions = [profile.c.refid == refid] if refid else []
            result = await self.execute(profile.select().where(*conditions))
            if result is None:
                return []
            return [(row["refid"], row["data"]) for row in result.fetchall()]

        if collection == "achievements":
            conditions = [achievement.c.type == self.GAME]
            if version:
                conditions.append(achievement.c.id == self._version_number(version))
            if refid:
                conditions.append(achievement.c.refid == refid)
            result = await self.execute(achievement.select().where(*conditions))
            if result is None:
                return []
            return [(row["refid"], row["data"]) for row in result.fetchall()]

        conditions = [
            konami_document.c.game_code == game_code,
            konami_document.c.collection == collection,
        ]
        if version:
            conditions.append(konami_document.c.version == version)
        if refid:
            conditions.append(konami_document.c.refid == refid)
        result = await self.execute(
            konami_document.select().where(*conditions).order_by(konami_document.c.id)
        )
        if result is None:
            return []
        return [(row["refid"], row["document"]) for row in result.fetchall()]
