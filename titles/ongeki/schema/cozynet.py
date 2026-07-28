from sqlalchemy import Column, Table, UniqueConstraint, func
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Integer, String

from artemis.data.schema import BaseData, metadata

nameplates: Table = Table(
    "cozynet_static_ongeki_nameplates",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column(
        "opt",
        ForeignKey("ongeki_static_opt.id", ondelete="SET NULL", onupdate="cascade"),
    ),
    Column("nameplateId", Integer, nullable=False),
    Column("name", String(255)),
    Column("description", String(255)),
    Column("imagePath", String(255)),
    UniqueConstraint(
        "version", "nameplateId", name="cozynet_static_ongeki_nameplates_uk"
    ),
    mysql_charset="utf8mb4",
)


class CozynetStaticOngekiData(BaseData):
    async def put_nameplate(
        self,
        version: int,
        opt_id: int | None,
        nameplate_id: int,
        name: str | None,
        description: str | None,
        image_path: str | None = None,
    ):
        query = insert(nameplates).values(
            version=version,
            opt=opt_id,
            nameplateId=nameplate_id,
            name=name,
            description=description,
            imagePath=image_path,
        )
        query = query.on_duplicate_key_update(
            opt=func.coalesce(nameplates.c.opt, query.inserted.opt),
            name=query.inserted.name,
            description=query.inserted.description,
            imagePath=query.inserted.imagePath,
        )
        result = await self.execute(query)

        if result is None:
            return None

        return result.inserted_primary_key.id

    async def set_nameplate_image_path(self, nameplate_id: int, image_path: str):
        sql = nameplates.update(nameplates.c.nameplateId == nameplate_id).values(
            imagePath=image_path
        )
        result = await self.execute(sql)

        return result is not None
