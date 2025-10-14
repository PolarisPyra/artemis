from typing import Optional

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row, RowMapping

from core.data.schema import BaseData, metadata

character: Table = Table(
    "daphnis_static_character",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("characterId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("sortName", String(255), nullable=False),
    Column("rareType", Integer, nullable=False),
    Column("works", String(255), nullable=True),
    Column("illustratorName", String(255), nullable=True),
    Column("imagePath", String(255), nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "characterId", name="daphnis_static_character_uk"),
    mysql_charset="utf8mb4",
)

nameplate: Table = Table(
    "daphnis_static_nameplate",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("nameplateId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("sortName", String(255), nullable=False),
    Column("explainText", String(255), nullable=False),
    Column("imagePath", String(255), nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "nameplateId", name="daphnis_static_nameplate_uk"),
    mysql_charset="utf8mb4",
)

system_voice: Table = Table(
    "daphnis_static_system_voice",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("systemVoiceId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("explainText", String(255), nullable=False),
    Column("imagePath", String(255), nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "systemVoiceId", name="daphnis_static_system_voice_uk"),
    mysql_charset="utf8mb4",
)

map_icon: Table = Table(
    "daphnis_static_map_icon",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("mapIconId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("sortName", String(255), nullable=False),
    Column("explainText", String(255), nullable=False),
    Column("imagePath", String(255), nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "mapIconId", name="daphnis_static_map_icon_uk"),
    mysql_charset="utf8mb4",
)

trophy: Table = Table(
    "daphnis_static_trophy",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("trophyId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("explainText", String(255), nullable=False),
    Column("rareType", Integer, nullable=False),
    Column("imagePath", String(255), nullable=True),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "trophyId", name="daphnis_static_trophy_uk"),
    mysql_charset="utf8mb4",
)

ticket: Table = Table(
    "daphnis_static_ticket",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("ticketId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("type", Integer, nullable=False),
    Column("target", Integer, nullable=False),
    Column("stockMaxNum", Integer, nullable=False),
    Column("explainText", String(255), nullable=False),
    Column("imagePath", String(255), nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "ticketId", name="daphnis_static_ticket_uk"),
    mysql_charset="utf8mb4",
)

skill: Table = Table(
    "daphnis_static_skill",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("skillId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("skillVersion", Integer, nullable=True),
    Column("categoryId", Integer, nullable=False),
    Column("categoryName", String(255), nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    UniqueConstraint("version", "skillId", name="daphnis_static_skill_uk"),
    mysql_charset="utf8mb4",
)

option: Table = Table(
    "daphnis_user_option",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("key", String(255), nullable=False),
    Column("value", String(255), nullable=True),
    UniqueConstraint("user", "key", name="daphnis_user_option_uk"),
    mysql_charset="utf8mb4",
)

recommendations: Table = Table(
    "daphnis_user_music_recommendations",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "user",
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("game", String(255), nullable=False),
    Column("musicId", Integer, nullable=False),
    Column("level", Integer, nullable=False),
    UniqueConstraint(
        "user", "game", "musicId", "level", name="daphnis_user_music_recommendations_uk"
    ),
    mysql_charset="utf8mb4",
)


stages: Table = Table(
    "daphnis_static_stages",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column(
        "opt",
        ForeignKey("chuni_static_opts.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    Column("stageId", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("imagePath", String(255), nullable=True),
    UniqueConstraint("version", "stageId", name="daphnis_static_stages_uk"),
    mysql_charset="utf8mb4",
)


class DaphnisStaticData(BaseData):
    async def put_character(
        self,
        version: int,
        character_id: int,
        name: str,
        sort_name: str,
        rare_type: int,
        works: Optional[str],
        illustrator_name: Optional[str],
        image_path: str,
        opt_id: int | None,
    ):
        query = insert(character).values(
            version=version,
            characterId=character_id,
            name=name,
            sortName=sort_name,
            rareType=rare_type,
            works=works,
            illustratorName=illustrator_name,
            imagePath=image_path,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            sortName=query.inserted.sortName,
            rareType=query.inserted.rareType,
            works=query.inserted.works,
            illustratorName=query.inserted.illustratorName,
            imagePath=query.inserted.imagePath,
            opt=func.coalesce(character.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_nameplate(
        self,
        version: int,
        nameplate_id: int,
        name: str,
        sort_name: str,
        explain_text: str,
        image_path: str,
        opt_id: int | None,
    ):
        query = insert(nameplate).values(
            version=version,
            nameplateId=nameplate_id,
            name=name,
            sortName=sort_name,
            explainText=explain_text,
            imagePath=image_path,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            sortName=query.inserted.sortName,
            explainText=query.inserted.explainText,
            imagePath=query.inserted.imagePath,
            opt=func.coalesce(nameplate.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_system_voice(
        self,
        version: int,
        system_voice_id: int,
        name: str,
        explain_text: str,
        image_path: str,
        opt_id: int | None,
    ):
        query = insert(system_voice).values(
            version=version,
            systemVoiceId=system_voice_id,
            name=name,
            explainText=explain_text,
            imagePath=image_path,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            explainText=query.inserted.explainText,
            imagePath=query.inserted.imagePath,
            opt=func.coalesce(system_voice.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_map_icon(
        self,
        version: int,
        map_icon_id: int,
        name: str,
        sort_name: str,
        explain_text: str,
        image_path: str,
        opt_id: int | None,
    ):
        query = insert(map_icon).values(
            version=version,
            mapIconId=map_icon_id,
            name=name,
            sortName=sort_name,
            explainText=explain_text,
            imagePath=image_path,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            sortName=query.inserted.sortName,
            explainText=query.inserted.explainText,
            imagePath=query.inserted.imagePath,
            opt=func.coalesce(map_icon.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_trophy(
        self,
        version: int,
        trophy_id: int,
        name: str,
        explain_text: str,
        rare_type: int,
        image_path: Optional[str],
        opt_id: int | None,
    ):
        query = insert(trophy).values(
            version=version,
            trophyId=trophy_id,
            name=name,
            explainText=explain_text,
            rareType=rare_type,
            imagePath=image_path,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            explainText=query.inserted.explainText,
            rareType=query.inserted.rareType,
            imagePath=query.inserted.imagePath,
            opt=func.coalesce(trophy.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def put_ticket(
        self,
        version: int,
        ticket_id: int,
        name: str,
        type: int,
        target: int,
        stock_max_num: int,
        explain_text: str,
        image_path: str,
        opt_id: int | None,
    ):
        query = insert(ticket).values(
            version=version,
            ticketId=ticket_id,
            name=name,
            type=type,
            target=target,
            stockMaxNum=stock_max_num,
            explainText=explain_text,
            imagePath=image_path,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            type=query.inserted.type,
            target=query.inserted.target,
            stockMaxNum=query.inserted.stockMaxNum,
            explainText=query.inserted.explainText,
            imagePath=query.inserted.imagePath,
            opt=func.coalesce(ticket.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def get_ticket(
        self,
        version: int,
        type: Optional[list[int]] = None,
        can_be_stocked: Optional[bool] = None,
    ) -> Optional[list[Row]]:
        cond = ticket.c.version == version

        if type is not None:
            cond &= ticket.c.type.in_(type)

        if can_be_stocked is True:
            cond &= ticket.c.stockMaxNum > 0
        elif can_be_stocked is False:
            cond &= ticket.c.stockMaxNum == 0

        query = ticket.select().where(cond)
        result = await self.execute(query)

        if result is None:
            return None

        return result.fetchall()

    async def put_skill(
        self,
        version: int,
        skill_id: int,
        name: str,
        skill_version: Optional[int],
        category_id: int,
        category_name: str,
        opt_id: int | None,
    ):
        query = insert(skill).values(
            version=version,
            skillId=skill_id,
            name=name,
            skillVersion=skill_version,
            categoryId=category_id,
            categoryName=category_name,
            opt=opt_id,
        )
        query = query.on_duplicate_key_update(
            name=query.inserted.name,
            skillVersion=query.inserted.skillVersion,
            categoryId=query.inserted.categoryId,
            categoryName=query.inserted.categoryName,
            opt=func.coalesce(skill.c.opt, query.inserted.opt),
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def get_option(self, user: int, key: str) -> Optional[str]:
        query = option.select().where((option.c.user == user) & (option.c.key == key))
        result = await self.execute(query)

        if result is None:
            return None

        row = result.fetchone()

        return row.value if row is not None else None

    async def get_recommendations(
        self, user: int, game: str
    ) -> Optional[list[RowMapping]]:
        query = recommendations.select().where(
            (recommendations.c.user == user) & (recommendations.c.game == game)
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.mappings().fetchall()

    async def put_stage(
        self,
        version: int,
        stage_id: int,
        name: str,
        image_path: str | None,
        opt_id: int | None,
    ):
        query = insert(stages).values(
            version=version,
            opt=opt_id,
            stageId=stage_id,
            name=name,
            imagePath=image_path,
        )
        query = query.on_duplicate_key_update(
            opt=func.coalesce(stages.c.opt, query.inserted.opt),
            name=query.inserted.name,
            imagePath=query.inserted.imagePath,
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id
