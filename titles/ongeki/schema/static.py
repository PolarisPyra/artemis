from typing import Dict, List, Optional, cast
from sqlalchemy import Table, Column, UniqueConstraint, PrimaryKeyConstraint, and_, text
from sqlalchemy.types import Integer, String, TIMESTAMP, Boolean, JSON, Float
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.engine import Row
from sqlalchemy.dialects.mysql import BIGINT, insert

from core.data.schema import BaseData, metadata
from core.data.schema.arcade import machine

options: Table = Table(
    "ongeki_static_opt",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("name", String(4), nullable=False),
    Column("sequence", Integer, nullable=False),
    Column("cmReleaseVer", Integer, nullable=False),
    Column("whenRead", TIMESTAMP, nullable=False, server_default=func.now()),
    Column("isEnable", Boolean, nullable=False, server_default=text("1")),
    UniqueConstraint("version", "name", name="ongeki_static_opt_uk"),
    mysql_charset="utf8mb4",
)

cm_options: Table = Table(
    "cm_static_opts",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("name", String(4), nullable=False),  # Axxx
    Column("sequence", Integer),  # Not all opts have a DataConfig.xml
    Column("gekiVersion", Integer),  # GEKI/DataConfig.xml
    Column("gekiReleaseVer", Integer),  # GEKI/DataConfig.xml
    Column("maiVersion", Integer),  # MAI/DataConfig.xml
    Column("maiReleaseVer", Integer),  # MAI/DataConfig.xml
    Column("whenRead", TIMESTAMP, nullable=False, server_default=func.now()),
    Column("isEnable", Boolean, nullable=False, server_default="1"),
    UniqueConstraint("version", "name", name="cm_static_opts_uk"),
    mysql_charset="utf8mb4",
)


events: Table = Table(
    "ongeki_static_events",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer),
    Column("eventId", Integer),
    Column("type", Integer),
    Column("name", String(255)),
    Column("startDate", TIMESTAMP, server_default=func.now()),
    Column("endDate", TIMESTAMP, server_default=func.now()),
    Column("enabled", Boolean, server_default="1"),
    Column(
        "opt",
        ForeignKey("ongeki_static_opt.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "eventId", "type", name="ongeki_static_events_uk"),
    mysql_charset="utf8mb4",
)


music: Table = Table(
    "ongeki_static_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer),
    Column("songId", Integer),
    Column("chartId", Integer),
    Column("title", String(255)),
    Column("artist", String(255)),
    Column("genre", String(255)),
    Column("level", Float),
    Column("noteCount", Integer),
    Column("jacketPath", String(255)),
    Column(
        "opt",
        ForeignKey("ongeki_static_opt.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "songId", "chartId", name="ongeki_static_music_uk"),
    mysql_charset="utf8mb4",
)

gachas = Table(
    "ongeki_static_gachas",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("gachaId", Integer, nullable=False),
    Column("gachaName", String(255), nullable=False),
    Column("type", Integer, nullable=False, server_default="0"),
    Column("kind", Integer, nullable=False, server_default="0"),
    Column("isCeiling", Boolean, server_default="0"),
    Column("maxSelectPoint", Integer, server_default="0"),
    Column("ceilingCnt", Integer, server_default="10"),
    Column("changeRateCnt1", Integer, server_default="0"),
    Column("changeRateCnt2", Integer, server_default="0"),
    Column("startDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("endDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("noticeStartDate", TIMESTAMP, server_default="2018-01-01 00:00:00.0"),
    Column("noticeEndDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column("convertEndDate", TIMESTAMP, server_default="2038-01-01 00:00:00.0"),
    Column(
        "opt", ForeignKey("cm_static_opts.id", ondelete="SET NULL", onupdate="cascade")
    ),
    UniqueConstraint("version", "gachaId", "gachaName", name="ongeki_static_gachas_uk"),
    mysql_charset="utf8mb4",
)

gacha_cards = Table(
    "ongeki_static_gacha_cards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("gachaId", Integer, nullable=False),
    Column("cardId", Integer, nullable=False),
    Column("rarity", Integer, nullable=False),
    Column("weight", Integer, server_default="1"),
    Column("isPickup", Boolean, server_default="0"),
    Column("isSelect", Boolean, server_default="0"),
    UniqueConstraint("gachaId", "cardId", name="ongeki_static_gacha_cards_uk"),
    mysql_charset="utf8mb4",
)

cards: Table = Table(
    "ongeki_static_cards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("cardId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("charaId", Integer, nullable=False),
    Column("nickName", String(255)),
    Column("school", String(255), nullable=False),
    Column("attribute", String(5), nullable=False),
    Column("gakunen", String(255), nullable=False),
    Column("rarity", Integer, nullable=False),
    Column("levelParam", String(255), nullable=False),
    Column("skillId", Integer, nullable=False),
    Column("choKaikaSkillId", Integer, nullable=False),
    Column("cardNumber", String(255)),
    Column("imagePath", String(255)),
    Column(
        "opt",
        ForeignKey("ongeki_static_opt.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "cardId", name="ongeki_static_cards_uk"),
    mysql_charset="utf8mb4",
)

music_ranking = Table(
    "ongeki_static_music_ranking_list",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("musicId", Integer, nullable=False),
    Column("point", Integer, nullable=False),
    Column("userName", String(255)),
    UniqueConstraint("version", "musicId", name="ongeki_static_music_ranking_uk"),
    mysql_charset="utf8mb4",
)

rewards: Table = Table(
    "ongeki_static_rewards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("rewardId", Integer, nullable=False),
    Column("rewardname", String(255), nullable=False),
    Column("itemKind", Integer, nullable=False),
    Column("itemId", Integer, nullable=False),
    Column(
        "opt",
        ForeignKey("ongeki_static_opt.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "rewardId", name="ongeki_static_rewards_uk"),
    mysql_charset="utf8mb4",
)

present = Table(
    "ongeki_static_present_list",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("presentId", Integer, nullable=False),
    Column("presentName", String(255), nullable=False),
    Column("rewardId", Integer, nullable=False),
    Column("stock", Integer, nullable=False),
    Column("message", String(255)),
    Column("startDate", String(25), nullable=False),
    Column("endDate", String(25), nullable=False),
    UniqueConstraint("version", "presentId", name="ongeki_static_present_list_uk"),
    mysql_charset="utf8mb4",
)

tech_music = Table(
    "ongeki_static_tech_music",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("eventId", Integer, nullable=False),
    Column("musicId", Integer, nullable=False),
    Column("level", Integer, nullable=False),
    UniqueConstraint("version", "musicId", name="ongeki_static_tech_music_uk"),
    mysql_charset="utf8mb4",
)

client_testmode = Table(
    "ongeki_static_client_testmode",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("regionId", Integer, nullable=False),
    Column("placeId", Integer, nullable=False),
    Column("clientId", String(11), nullable=False),
    Column("updateDate", TIMESTAMP, nullable=False),
    Column("isDelivery", Boolean, nullable=False),
    Column("groupId", Integer, nullable=False),
    Column("groupRole", Integer, nullable=False),
    Column("continueMode", Integer, nullable=False),
    Column("selectMusicTime", Integer, nullable=False),
    Column("advertiseVolume", Integer, nullable=False),
    Column("eventMode", Integer, nullable=False),
    Column("eventMusicNum", Integer, nullable=False),
    Column("patternGp", Integer, nullable=False),
    Column("limitGp", Integer, nullable=False),
    Column("maxLeverMovable", Integer, nullable=False),
    Column("minLeverMovable", Integer, nullable=False),
    UniqueConstraint("clientId", name="ongeki_static_client_testmode_uk"),
    mysql_charset="utf8mb4",
)

game_point = Table(
    "ongeki_static_game_point",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("type", Integer, nullable=False),
    Column("cost", Integer, nullable=False),
    Column(
        "startDate", String(25), nullable=False, server_default="2000-01-01 05:00:00.0"
    ),
    Column(
        "endDate", String(25), nullable=False, server_default="2099-01-01 05:00:00.0"
    ),
    UniqueConstraint("type", name="ongeki_static_game_point_uk"),
    mysql_charset="utf8mb4",
)


class OngekiStaticData(BaseData):
    async def put_card(
        self, version: int, card_id: int, opt_id: int | None, **card_data
    ) -> Optional[int]:
        sql = insert(cards).values(
            version=version, cardId=card_id, opt=opt_id, **card_data
        )

        conflict = sql.on_duplicate_key_update(
            opt=func.coalesce(cards.c.opt, opt_id), **card_data
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert card! card_id {card_id}")
            return None
        return result.lastrowid

    async def set_card_image_path(self, card_id: int, image_path: str):
        sql = cards.update(cards.c.cardId == card_id).values(imagePath=image_path)
        result = await self.execute(sql)

        return result is not None

    async def get_card(self, version: int, card_id: int) -> Optional[Dict]:
        sql = cards.select(and_(cards.c.version <= version, cards.c.cardId == card_id))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_card_by_card_number(
        self, version: int, card_number: str
    ) -> Optional[Dict]:
        if not card_number.startswith("[O.N.G.E.K.I.]"):
            card_number = f"[O.N.G.E.K.I.]{card_number}"

        sql = cards.select(
            and_(cards.c.version <= version, cards.c.cardNumber == card_number)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_card_by_name(self, version: int, name: str) -> Optional[Dict]:
        sql = cards.select(and_(cards.c.version <= version, cards.c.name == name))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_cards(self, version: int) -> Optional[List[Dict]]:
        sql = cards.select(cards.c.version <= version)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_cards_by_rarity(
        self, version: int, rarity: int
    ) -> Optional[List[Dict]]:
        sql = cards.select(and_(cards.c.version <= version, cards.c.rarity == rarity))

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_gacha(
        self,
        version: int,
        gacha_id: int,
        gacha_name: int,
        gacha_kind: int,
        **gacha_data,
    ) -> Optional[int]:
        sql = insert(gachas).values(
            version=version,
            gachaId=gacha_id,
            gachaName=gacha_name,
            kind=gacha_kind,
            **gacha_data,
        )

        conflict = sql.on_duplicate_key_update(
            version=version,
            gachaId=gacha_id,
            gachaName=gacha_name,
            kind=gacha_kind,
            **gacha_data,
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert gacha! gacha_id {gacha_id}")
            return None
        return result.lastrowid

    async def get_gacha(self, version: int, gacha_id: int) -> Optional[Dict]:
        sql = gachas.select(
            and_(gachas.c.version <= version, gachas.c.gachaId == gacha_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def get_gachas(self, version: int) -> Optional[List[Dict]]:
        sql = gachas.select(gachas.c.version == version).order_by(
            gachas.c.gachaId.asc()
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_gacha_card(
        self, gacha_id: int, card_id: int, **gacha_card
    ) -> Optional[int]:
        sql = insert(gacha_cards).values(gachaId=gacha_id, cardId=card_id, **gacha_card)

        conflict = sql.on_duplicate_key_update(
            gachaId=gacha_id, cardId=card_id, **gacha_card
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert gacha card! gacha_id {gacha_id}")
            return None
        return result.lastrowid

    async def get_gacha_cards(self, gacha_id: int) -> Optional[List[Dict]]:
        sql = gacha_cards.select(gacha_cards.c.gachaId == gacha_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_event(
        self,
        version: int,
        event_id: int,
        event_type: int,
        event_name: str,
        opt_id: int | None,
        *,
        enabled: bool = True,
    ) -> Optional[int]:
        sql = insert(events).values(
            version=version,
            eventId=event_id,
            type=event_type,
            name=event_name,
            endDate=f"2038-01-01 00:00:00",
            enabled=enabled,
            opt=opt_id,
        )

        conflict = sql.on_duplicate_key_update(
            name=event_name, opt=func.coalesce(events.c.opt, opt_id)
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert event! event_id {event_id}")
            return None
        return result.lastrowid

    async def get_event(self, version: int, event_id: int) -> Optional[List[Dict]]:
        sql = select(events).where(
            and_(events.c.version == version, events.c.eventId == event_id)
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_events(self, version: int) -> Optional[List[Dict]]:
        sql = select(events).where(events.c.version == version)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_enabled_events(self, version: int) -> Optional[List[Dict]]:
        sql = select(events).where(
            and_(events.c.version == version, events.c.enabled.is_(True))
        )

        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_chart(
        self,
        version: int,
        song_id: int,
        chart_id: int,
        title: str,
        artist: str,
        genre: str,
        level: float,
        note_count: int,
        opt_id: int | None,
    ) -> Optional[int]:
        sql = insert(music).values(
            version=version,
            songId=song_id,
            chartId=chart_id,
            title=title,
            artist=artist,
            genre=genre,
            level=level,
            noteCount=note_count,
            opt=opt_id,
        )

        conflict = sql.on_duplicate_key_update(
            title=title,
            artist=artist,
            genre=genre,
            level=level,
            noteCount=note_count,
            opt=func.coalesce(music.c.opt, opt_id),
        )

        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(
                f"Failed to insert chart! song_id: {song_id}, chart_id: {chart_id}"
            )
            return None
        return result.lastrowid

    async def set_chart_jacket_path(self, version: int, song_id: int, jacket_path: str):
        sql = music.update(
            (music.c.version == version) & (music.c.songId == song_id)
        ).values(jacketPath=jacket_path)
        result = await self.execute(sql)

        return result is not None

    async def get_chart(
        self, version: int, song_id: int, chart_id: int = None
    ) -> Optional[List[Dict]]:
        pass

    async def get_music(self, version: int) -> Optional[List[Dict]]:
        pass

    async def get_music_chart(
        self, version: int, song_id: int, chart_id: int
    ) -> Optional[List[Row]]:
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

    async def get_ranking_list(self, version: int) -> Optional[List[Dict]]:
        sql = select(
            music_ranking.c.musicId.label("id"),
            music_ranking.c.point,
            music_ranking.c.userName,
        ).where(music_ranking.c.version == version)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_reward(
        self,
        version: int,
        rewardId: int,
        rewardname: str,
        itemKind: int,
        itemId: int,
        opt_id: int | None,
    ) -> Optional[int]:
        sql = insert(rewards).values(
            version=version,
            rewardId=rewardId,
            rewardname=rewardname,
            itemKind=itemKind,
            itemId=itemId,
            opt=opt_id,
        )
        conflict = sql.on_duplicate_key_update(
            rewardname=rewardname,
            opt=func.coalesce(rewards.c.opt, opt_id),
        )
        result = await self.execute(conflict)
        if result is None:
            self.logger.warning(f"Failed to insert reward! reward_id: {rewardId}")
            return None
        return result.lastrowid

    async def get_reward_list(self, version: int) -> Optional[List[Dict]]:
        sql = select(rewards).where(rewards.c.version == version)

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"Failed to load reward list")
            return None
        return result.fetchall()

    async def get_present_list(self, version: int) -> Optional[List[Dict]]:
        sql = select(present).where(present.c.version == version)

        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"Failed to load present list")
            return None
        return result.fetchall()

    async def get_tech_music(self, version: int) -> Optional[List[Dict]]:
        sql = select(tech_music).where(tech_music.c.version == version)

        result = await self.execute(sql)

        if result is None:
            return None
        return result.fetchall()

    async def put_client_testmode_data(
        self, region_id: int, client_testmode_data: Dict
    ) -> Optional[List[Dict]]:
        sql = insert(client_testmode).values(regionId=region_id, **client_testmode_data)
        conflict = sql.on_duplicate_key_update(
            regionId=region_id, **client_testmode_data
        )

        result = await self.execute(conflict)
        if result is None:
            (
                self.logger.warning(
                    f"region_id: {region_id} Failed to update ClientTestMode data"
                ),
            )
            return None
        return result.lastrowid

    async def put_client_setting_data(
        self, machine_id: int, client_setting_data: Dict
    ) -> Optional[List[Dict]]:
        sql = machine.update(machine.c.id == machine_id).values(
            data=client_setting_data
        )

        result = await self.execute(sql)
        if result is None:
            (
                self.logger.warning(
                    f"machine_id: {machine_id} Failed to update ClientSetting data"
                ),
            )
            return None
        return result.lastrowid

    async def put_static_game_point_defaults(self) -> Optional[List[Dict]]:
        game_point_defaults = [
            {"type": 0, "cost": 100},
            {"type": 1, "cost": 230},
            {"type": 2, "cost": 370},
            {"type": 3, "cost": 120},
            {"type": 4, "cost": 240},
            {"type": 5, "cost": 360},
        ]
        sql = insert(game_point).values(game_point_defaults)
        result = await self.execute(sql)
        if result is None:
            self.logger.warning(f"Failed to insert default GP table!")
            return None
        return result.lastrowid

    async def get_static_game_point(self) -> Optional[List[Dict]]:
        sql = select(
            game_point.c.type,
            game_point.c.cost,
            game_point.c.startDate,
            game_point.c.endDate,
        )
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def put_opt(
        self, version: int, name: str, sequence: int, card_maker_sequence: int
    ):
        sql = insert(options).values(
            version=version,
            name=name,
            sequence=sequence,
            cmReleaseVer=card_maker_sequence,
        )
        conflict = sql.on_duplicate_key_update(sequence=sequence, whenRead=func.now())
        result = await self.execute(conflict)

        if result is None:
            self.logger.warning(
                "Failed to insert option! version=%s name=%s sequence=%s card_maker_sequence=%s",
                version,
                name,
                sequence,
                card_maker_sequence,
            )
            return None

        return cast(int, result.lastrowid)

    async def get_opt_by_version_folder(self, version: int, name: str):
        result = await self.execute(
            options.select().where(
                (options.c.version == version) & (options.c.name == name)
            )
        )

        if result is None:
            return None

        return cast(Row, result.fetchone())
