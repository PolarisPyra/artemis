import re
from datetime import datetime
from sqlalchemy import Column, Table, and_, or_, UniqueConstraint
from typing import Optional, Dict, List
from sqlalchemy.sql.schema import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import Integer, String, Boolean, JSON, BOOLEAN, VARCHAR
from sqlalchemy.sql import func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.sql import func, select
from sqlalchemy.sql.schema import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import JSON, Boolean, Integer, String, BIGINT, INTEGER, CHAR, FLOAT, VARCHAR, TIMESTAMP

from core.data.schema.base import BaseData, metadata

arcade: Table = Table(
    "arcade",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("name", String(255)),
    Column("nickname", String(255)),
    Column("country", String(3)),
    Column("country_id", Integer),
    Column("state", String(255)),
    Column("city", String(255)),
    Column("region_id", Integer),
    Column("timezone", String(255)),
    Column("ip", String(39)),
    mysql_charset="utf8mb4",
)

machine: Table = Table(
    "machine",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column(
        "arcade",
        ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("serial", VARCHAR(16), nullable=False),
    Column("board", String(15)),
    Column("game", String(4)),
    Column("country", String(3)),  # overwrites if not null
    Column("timezone", String(255)),
    Column("memo", String(255)),
    Column("name", VARCHAR(25)), # for bemani cabs
    Column("is_cab", Boolean),
    Column("ota_channel", VARCHAR(260)),
    Column("paseli_enable", BOOLEAN),
    Column("data", JSON),
    mysql_charset="utf8mb4",
)

update: Table = Table(
    "machine_update",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("game", CHAR(4), nullable=False),
    Column("version", VARCHAR(15), nullable=False),
    Column("channel", VARCHAR(260), nullable=False),
    Column("app_ini", VARCHAR(260)),
    Column("opt_ini", VARCHAR(260)),
    UniqueConstraint("game", "version", "channel", name="machine_update_uk"),
    mysql_charset="utf8mb4",
)

arcade_owner: Table = Table(
    "arcade_owner",
    metadata,
    Column(
        "user",
        Integer,
        ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column(
        "arcade",
        Integer,
        ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("permissions", Integer, nullable=False),
    PrimaryKeyConstraint("user", "arcade", name="arcade_owner_pk"),
    mysql_charset="utf8mb4",
)

billing_charge: Table = Table(
    "machine_billing_charge",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column(
        "machine",
        Integer,
        ForeignKey("machine.id", ondelete="cascade", onupdate="cascade"),
        nullable=False,
    ),
    Column("game_id", CHAR(5), nullable=False),
    Column("game_ver", FLOAT, nullable=False),
    Column("play_count", INTEGER, nullable=False),
    Column("play_limit", INTEGER, nullable=False),
    Column("product_code", INTEGER, nullable=False),
    Column("product_count", INTEGER, nullable=False),
    Column("func_type", INTEGER, nullable=False),
    Column("player_number", INTEGER, nullable=False),
    Column("ins_datetime", TIMESTAMP, nullable=False, server_default=func.now()),
    mysql_charset="utf8mb4",
)

# These settings are only really of interest
# for real cabinets operating as pay-to-play
billing_credit: Table = Table(
    "machine_billing_credit",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column(
        "machine",
        Integer,
        ForeignKey("machine.id", ondelete="cascade", onupdate="cascade"),
        nullable=False
    ),
    Column("game_id", CHAR(5), nullable=False),
    Column("chute_type", INTEGER, nullable=False),
    Column("service_type", INTEGER, nullable=False),
    Column("operation_type", INTEGER, nullable=False),
    Column("coin_rate0", INTEGER, nullable=False),
    Column("coin_rate1", INTEGER, nullable=False),
    Column("coin_bonus", INTEGER, nullable=False),
    Column("credit_rate", INTEGER, nullable=False),
    Column("coin_count_slot0", INTEGER, nullable=False),
    Column("coin_count_slot1", INTEGER, nullable=False),
    Column("coin_count_slot2", INTEGER, nullable=False),
    Column("coin_count_slot3", INTEGER, nullable=False),
    Column("coin_count_slot4", INTEGER, nullable=False),
    Column("coin_count_slot5", INTEGER, nullable=False),
    Column("coin_count_slot6", INTEGER, nullable=False),
    Column("coin_count_slot7", INTEGER, nullable=False),
    Column("ins_datetime", TIMESTAMP, nullable=False, server_default=func.now()),
    Column("upd_datetime", TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()),
    UniqueConstraint("machine", "game_id", name="machine_billing_credit_uk"),
    mysql_charset="utf8mb4",
)

billing_playct: Table = Table(
    "machine_billing_playcount",
    metadata,
    Column("id", BIGINT, primary_key=True, nullable=False),
    Column(
        "machine",
        Integer,
        ForeignKey("machine.id", ondelete="cascade", onupdate="cascade"),
        nullable=False
    ),
    Column("game_id", CHAR(5), nullable=False),
    Column("year", INTEGER, nullable=False),
    Column("month", INTEGER, nullable=False),
    Column("playct", BIGINT, nullable=False, server_default="1"),
    Column("ins_datetime", TIMESTAMP, nullable=False, server_default=func.now()),
    Column("upd_datetime", TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()),
    UniqueConstraint("machine", "game_id", "year", "month", name="machine_billing_playcount_uk"),
    mysql_charset="utf8mb4",
)

class ArcadeData(BaseData):
    async def get_machine(self, serial: Optional[str] = None, id: Optional[int] = None) -> Optional[Row]:
        if serial is not None:
            serial = serial.replace("-", "")
            if len(serial) == 11:
                sql = machine.select(machine.c.serial.like(f"{serial}%"))

            elif len(serial) == 15:
                sql = machine.select(machine.c.serial == serial)

            else:
                self.logger.error(f"{__name__ }: Malformed serial {serial}")
                return None

        elif id is not None:
            sql = machine.select(machine.c.id == id)

        else:
            self.logger.error(f"{__name__ }: Need either serial or ID to look up!")
            return None

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def create_machine(
        self,
        arcade_id: int,
        serial: str = "",
        board: Optional[str] = None,
        game: Optional[str] = None,
        is_cab: bool = False,
    ) -> Optional[int]:
        if not arcade_id:
            self.logger.error(f"{__name__ }: Need arcade id!")
            return None

        sql = machine.insert().values(
            arcade=arcade_id, serial=serial, board=board, game=game, is_cab=is_cab
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def set_machine_arcade(self, machine_id: int, new_arcade: int) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(arcade = new_arcade)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} arcade to {new_arcade}")
            return False
        return True

    async def set_machine_serial(self, machine_id: int, serial: str) -> None:
        result = await self.execute(
            machine.update(machine.c.id == machine_id).values(keychip=serial)
        )
        if result is None:
            self.logger.error(
                f"Failed to update serial for machine {machine_id} -> {serial}"
            )
        return result.lastrowid

    async def set_machine_boardid(self, machine_id: int, boardid: str) -> None:
        result = await self.execute(
            machine.update(machine.c.id == machine_id).values(board=boardid)
        )
        if result is None:
            self.logger.error(
                f"Failed to update board id for machine {machine_id} -> {boardid}"
            )

    async def set_machine_game(self, machine_id: int, new_game: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(game = new_game)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} game to {new_game}")
            return False
        return True

    async def set_machine_country(self, machine_id: int, new_country: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(country = new_country)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} country to {new_country}")
            return False
        return True

    async def set_machine_timezone(self, machine_id: int, new_timezone: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(timezone = new_timezone)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} timezone to {new_timezone}")
            return False
        return True

    async def set_machine_real_cabinet(self, machine_id: int, is_real: bool = False) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(is_cab = is_real)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} is_cab to {is_real}")
            return False
        return True

    async def set_machine_ota_channel(self, machine_id: int, channel_name: Optional[str] = None) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(ota_channel = channel_name)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} ota channel to {channel_name}")
            return False
        return True

    async def set_machine_memo(self, machine_id: int, new_memo: Optional[str]) -> bool:
        sql = machine.update(machine.c.id == machine_id).values(memo = new_memo)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update machine {machine_id} memo")
            return False
        return True

    async def get_arcade(self, id: int) -> Optional[Row]:
        sql = arcade.select(arcade.c.id == id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()
    
    async def get_arcade_machines(self, id: int) -> Optional[List[Row]]:
        sql = machine.select(machine.c.arcade == id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def create_arcade(
        self,
        name: Optional[str] = None,
        nickname: Optional[str] = None,
        country: str = "JPN",
        country_id: int = 1,
        state: str = "",
        city: str = "",
        region_id: int = 1,
    ) -> Optional[int]:
        if nickname is None:
            nickname = name

        sql = arcade.insert().values(
            name=name,
            nickname=nickname,
            country=country,
            country_id=country_id,
            state=state,
            city=city,
            region_id=region_id,
        )

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def get_arcades_managed_by_user(self, user_id: int) -> Optional[List[Row]]:
        sql = select(arcade).join(arcade_owner, arcade_owner.c.arcade == arcade.c.id).where(arcade_owner.c.user == user_id)
        result = await self.execute(sql)
        if result is None:
            return False
        return result.fetchall()
    
    async def get_manager_permissions(self, user_id: int, arcade_id: int) -> Optional[int]:
        sql = select(arcade_owner.c.permissions).where(and_(arcade_owner.c.user == user_id, arcade_owner.c.arcade == arcade_id))
        result = await self.execute(sql)
        if result is None:
            return None
        row =  result.fetchone()
        if row:
            return row['permissions']
        return None

    async def get_arcade_owners(self, arcade_id: int) -> Optional[Row]:
        sql = select(arcade_owner).where(arcade_owner.c.arcade == arcade_id)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def add_arcade_owner(self, arcade_id: int, user_id: int, permissions: int = 1) -> Optional[int]:
        sql = insert(arcade_owner).values(arcade=arcade_id, user=user_id, permissions=permissions)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.lastrowid

    async def set_arcade_owner_permissions(self, arcade_id: int, user_id: int, new_permissions: int = 1) -> bool:
        sql = arcade_owner.update(
            and_(arcade_owner.c.arcade == arcade_id, arcade_owner.c.user == user_id)
        ).values(permissions = new_permissions)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade owner permissions to {new_permissions} for user {user_id} arcade {arcade_id}")
            return False
        return True

    async def get_arcade_by_name(self, name: str) -> Optional[List[Row]]:
        sql = arcade.select(or_(arcade.c.name.like(f"%{name}%"), arcade.c.nickname.like(f"%{name}%")))
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def get_arcades_by_ip(self, ip: str) -> Optional[List[Row]]:
        sql = arcade.select().where(arcade.c.ip == ip)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def set_arcade_name_nickname(self, arcade_id: int, new_name: Optional[str], new_nickname: Optional[str]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(name = new_name, nickname = new_nickname)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} name to {new_name}/{new_nickname}")
            return False
        return True

    async def set_arcade_region_info(self, arcade_id: int, new_country: Optional[str], new_state: Optional[str], new_city: Optional[str], new_region_id: Optional[int], new_country_id: Optional[int]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(
            country = new_country,
            state = new_state,
            city = new_city,
            region_id = new_region_id,
            country_id = new_country_id
        )
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} regional info to {new_country}/{new_state}/{new_city}/{new_region_id}/{new_country_id}")
            return False
        return True

    async def set_arcade_timezone(self, arcade_id: int, new_timezone: Optional[str]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(timezone = new_timezone)
        
        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} timezone to {new_timezone}")
            return False
        return True

    async def set_arcade_vpn_ip(self, arcade_id: int, new_ip: Optional[str]) -> bool:
        sql = arcade.update(arcade.c.id == arcade_id).values(ip = new_ip)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to update arcade {arcade_id} VPN address to {new_ip}")
            return False
        return True

    async def get_num_generated_keychips(self) -> Optional[int]:
        result = await self.execute(select(func.count("serial LIKE 'A69A%'")).select_from(machine))
        if result:
            return result.fetchone()['count_1']
        self.logger.error("Failed to count machine serials that start with A69A!")

    async def billing_add_charge(self, machine_id: int, game_id: str, game_ver: float, playcount: int, playlimit, product_code: int, product_count: int, func_type: int, player_num: int) -> Optional[int]:
        result = await self.execute(billing_charge.insert().values(
            machine=machine_id,
            game_id=game_id,
            game_ver=game_ver,
            play_count=playcount,
            play_limit=playlimit,
            product_code=product_code,
            product_count=product_count,
            func_type=func_type,
            player_number=player_num
        ))

        if result is None:
            self.logger.error(f"Failed to add billing charge for machine {machine_id}!")
            return None
        return result.lastrowid

    async def billing_get_last_charge(self, machine_id: int, game_id: str) -> Optional[Row]:
        result = await self.execute(billing_charge.select(
            and_(billing_charge.c.machine == machine_id, billing_charge.c.game_id == game_id)
        ).order_by(billing_charge.c.id.desc()).limit(3))
        if result:
            return result.fetchone()

    async def billing_set_credit(self, machine_id: int, game_id: str, chute_type: int, service_type: int, op_mode: int, coin_rate0: int, coin_rate1: int,
        bonus_adder: int, coin_to_credit_rate: int, coin_count_slot0: int, coin_count_slot1: int, coin_count_slot2: int, coin_count_slot3: int,
        coin_count_slot4: int, coin_count_slot5: int, coin_count_slot6: int, coin_count_slot7: int) -> Optional[int]:
        
        sql = insert(billing_credit).values(
            machine=machine_id,
            game_id=game_id,
            chute_type=chute_type,
            service_type=service_type,
            operation_type=op_mode,
            coin_rate0=coin_rate0,
            coin_rate1=coin_rate1,
            coin_bonus=bonus_adder,
            credit_rate=coin_to_credit_rate,
            coin_count_slot0=coin_count_slot0,
            coin_count_slot1=coin_count_slot1,
            coin_count_slot2=coin_count_slot2,
            coin_count_slot3=coin_count_slot3,
            coin_count_slot4=coin_count_slot4,
            coin_count_slot5=coin_count_slot5,
            coin_count_slot6=coin_count_slot6,
            coin_count_slot7=coin_count_slot7,
        )

        conflict = sql.on_duplicate_key_update(
            chute_type=chute_type,
            service_type=service_type,
            operation_type=op_mode,
            coin_rate0=coin_rate0,
            coin_rate1=coin_rate1,
            coin_bonus=bonus_adder,
            credit_rate=coin_to_credit_rate,
            coin_count_slot0=coin_count_slot0,
            coin_count_slot1=coin_count_slot1,
            coin_count_slot2=coin_count_slot2,
            coin_count_slot3=coin_count_slot3,
            coin_count_slot4=coin_count_slot4,
            coin_count_slot5=coin_count_slot5,
            coin_count_slot6=coin_count_slot6,
            coin_count_slot7=coin_count_slot7,
            upd_datetime=datetime.now()
        )
        
        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to set billing credit settings for machine {machine_id}!")
            return None
        return result.lastrowid

    async def billing_get_credit(self, machine_id: int, game_id: str) -> Optional[Row]:
        result = await self.execute(billing_credit.select(
            and_(billing_credit.c.machine == machine_id, billing_credit.c.game_id == game_id)
        ))
        if result:
            return result.fetchone()

    async def billing_add_playcount(self, machine_id: int, game_id: str, playct: int = 1) -> None:
        now = datetime.now()
        sql = insert(billing_playct).values(
            machine=machine_id,
            game_id=game_id,
            year=now.year,
            month=now.month,
            playct=playct
        )

        conflict = sql.on_duplicate_key_update(
            playct=billing_playct.c.playct + playct,
            upd_datetime=datetime.now()
        )
        result = await self.execute(conflict)

        if result is None:
            self.logger.error(f"Failed to add playcount for machine {machine_id} running {game_id}")

    async def billing_get_playcount_3mo(self, machine_id: int, game_id: str) -> Optional[List[Row]]:
        result = await self.execute(billing_playct.select(and_(
            billing_playct.c.machine == machine_id,
            billing_playct.c.game_id == game_id
        )).order_by(billing_playct.c.year.desc(), billing_playct.c.month.desc()).limit(3))

        if result is not None:
            return result.fetchall()

    async def billing_get_last_playcount(self, machine_id: int, game_id: str) -> Optional[Row]:
        result = await self.execute(billing_playct.select(and_(
            billing_playct.c.machine == machine_id,
            billing_playct.c.game_id == game_id
        )).order_by(billing_playct.c.year.desc(), billing_playct.c.month.desc()).limit(1))

        if result is not None:
            return result.fetchone()

    async def create_ota_update(self, game_id: str, ver: str, channel: str, app: Optional[str], opt: Optional[str] = None) -> Optional[int]:
        result = await self.execute(insert(update).values(
            game = game_id,
            version = ver,
            channel = channel,
            app_ini = app,
            opt_ini = opt
        ))

        if result is None:
            self.logger.error(f"Failed to create {game_id} v{ver} update on channel {channel}")
        return result.lastrowid

    async def get_ota_update(self, game_id: str, ver: str, channel: str) -> Optional[Row]:
        result = await self.execute(update.select(and_(
            and_(update.c.game == game_id, update.c.version == ver),
            update.c.channel == channel
        )))

        if result is None:
            return None
        return result.fetchone()

    def format_serial(
        self, platform_code: str, platform_rev: int, serial_letter: str, serial_num: int, append: int, dash: bool = False
    ) -> str:
        return f"{platform_code}{'-' if dash else ''}{platform_rev:02d}{serial_letter}{serial_num:04d}{append:04d}"

    def validate_keychip_format(self, serial: str) -> bool:
        # For the 2nd letter, E and X are the only "real" values that have been observed (A is used for generated keychips)
        if re.fullmatch(r"^A[0-9]{2}[A-Z][-]?[0-9]{2}[A-HJ-NP-Z][0-9]{4}([0-9]{4})?$", serial) is None:
            return False
        
        return True
    
    # Thanks bottersnike!
    def get_keychip_suffix(self, year: int, month: int) -> str:
        assert year > 1957
        assert 1 <= month <= 12

        year -= 1957
        # Jan/Feb/Mar are from the previous tax year
        if month < 4:
            year -= 1
        assert year >= 1 and year <= 99

        month = ((month - 1) + 9) % 12  # Offset so April=0
        return f"{year:02}{month // 6:01}{month % 6 + 1:01}"

    def parse_keychip_suffix(self, suffix: str) -> tuple[int, int]:
        year = int(suffix[0:2])
        half = int(suffix[2])
        assert half in (0, 1)
        period = int(suffix[3])
        assert period in (1, 2, 3, 4, 5, 6)

        month = half * 6 + (period - 1)
        month = ((month + 3) % 12) + 1  # Offset so Jan=1

        # Jan/Feb/Mar are from the previous tax year
        if month < 4:
            year += 1
        year += 1957

        return (year, month)

    async def get_bemani_machine(self, pcbid: str) -> Optional[Row]:
        cab_id = self.from_pcbid(pcbid)
        if not cab_id:
            return
        
        sql = machine.select(machine.c.serial == cab_id)
        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchone()

    async def set_bemani_machine_name(self, pcbid: str, new_name: str) -> None:
        cab_id = self.from_pcbid(pcbid)
        if not cab_id:
            return
        
        sql = machine.update(machine.c.serial == cab_id).values(
            name=new_name
        )

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to set machine {pcbid} name to {new_name}")

    async def set_bemani_machine_settings(self, pcbid: str, new_settings: Dict) -> None:
        cab_id = self.from_pcbid(pcbid)
        if not cab_id:
            return
        
        sql = machine.update(machine.c.serial == cab_id).values(
            data=new_settings
        )

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to set machine {pcbid} settings to {new_settings}")

    def gen_pcbid(self, cab_id: int) -> Optional[str]:
        """
        Ordinarily, the 5th digit must be either a 1 or a 2, but we can use this
        to quickly differentiate real PCBIDs from generated ones. Games don't seem to
        mind them being technically malformed in this way.
        """
        return f"012000{cab_id:14X}"
    
    def from_pcbid(self, pcbid: str) -> Optional[str]:
        if not pcbid.startswith("0120") and not len(pcbid) == 20:
            self.logger.error(f"Malformed PCB ID {pcbid}")
            return None
        
        return pcbid[-16:]