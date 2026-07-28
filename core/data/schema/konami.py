"""Generic JSON document storage for e-amusement profiles and game data."""

from sqlalchemy import Column, Integer, String, Table, UniqueConstraint
from sqlalchemy.types import JSON

from core.data.schema.base import BaseData, metadata


konami_document = Table(
    "konami_document", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("refid", String(32), nullable=False),
    Column("game_code", String(8), nullable=False),
    Column("collection", String(64), nullable=False),
    Column("version", String(32), nullable=False, default=""),
    Column("document", JSON, nullable=False),
    UniqueConstraint("refid", "game_code", "collection", "version", name="konami_document_uk"),
    mysql_charset="utf8mb4",
)


class KonamiData(BaseData):
    async def get_document(self, refid: str, game_code: str, collection: str, version: str = ""):
        result = await self.execute(konami_document.select().where(
            (konami_document.c.refid == refid) &
            (konami_document.c.game_code == game_code) &
            (konami_document.c.collection == collection) &
            (konami_document.c.version == version)
        ))
        row = result.fetchone() if result is not None else None
        return row["document"] if row is not None else None

    async def put_document(self, refid: str, game_code: str, collection: str, document: dict, version: str = ""):
        from sqlalchemy.dialects.mysql import insert
        statement = insert(konami_document).values(
            refid=refid, game_code=game_code, collection=collection,
            version=version, document=document,
        )
        return await self.execute(statement.on_duplicate_key_update(document=document))
