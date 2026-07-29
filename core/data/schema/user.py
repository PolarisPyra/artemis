from typing import List, Optional

import bcrypt
from sqlalchemy import Column, Table, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Row
from sqlalchemy.sql import func, select, and_, or_
from sqlalchemy.types import TIMESTAMP, Integer, String, BIGINT, INTEGER, CHAR, BOOLEAN
from datetime import datetime

from core.data.schema.base import BaseData, metadata, campaign, campaign_game

aime_user: Table = Table(
    "aime_user",
    metadata,
    Column("id", Integer, nullable=False, primary_key=True, autoincrement=True),
    Column("username", String(25), unique=True),
    Column("email", String(255), unique=True),
    Column("password", String(255)),
    Column("permissions", Integer),
    Column("created_date", TIMESTAMP, server_default=func.now()),
    Column("last_login_date", TIMESTAMP, onupdate=func.now()),
    Column("suspend_expire_time", TIMESTAMP),
    Column("pin", CHAR(4)),
    mysql_charset="utf8mb4",
)

refid = Table(
    "refid",
    metadata,
    Column("id", CHAR(16), nullable=False, primary_key=True),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("game", CHAR(3), nullable=False),
    Column("version", INTEGER, nullable=False),
    mysql_charset="utf8mb4",
)

paseli_sesh = Table(
    "paseli_session",
    metadata,
    Column("id", CHAR(16), nullable=False, primary_key=True),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("machine", INTEGER, ForeignKey("machine.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("game", CHAR(4), nullable=False),
    Column("opened", TIMESTAMP, nullable=False, server_default=func.now()),
    Column("closed", TIMESTAMP),
    mysql_charset="utf8mb4",
)

paseli_tx = Table(
    "paseli_transaction",
    metadata,
    Column("id", BIGINT, nullable=False, primary_key=True, autoincrement=True),
    Column("sesh_id", CHAR(16), ForeignKey("paseli_session.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("tx_num", INTEGER, nullable=False),
    Column("ammount", INTEGER, nullable=False),
    Column("detail", CHAR(255), nullable=False),
    Column("detail_readable", CHAR(255)),
    Column("when_charged", TIMESTAMP, nullable=False, server_default=func.now()),
    Column("when_refunded", TIMESTAMP),
    UniqueConstraint("sesh_id", "tx_num", name="paseli_transaction_uk"),
    mysql_charset="utf8mb4",
)

paseli_balance = Table(
    "paseli_balance",
    metadata,
    Column("id", BIGINT, nullable=False, primary_key=True, autoincrement=True),
    Column("user", INTEGER, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("arcade", INTEGER, ForeignKey("arcade.id", ondelete="cascade", onupdate="cascade")), # null = global balance
    Column("balance", INTEGER, nullable=False, server_default="0"),
    Column("ammount_added", BIGINT, nullable=False, server_default="0"),
    Column("ammount_spend", BIGINT, nullable=False, server_default="0"),
    Column("ammount_adjusted", BIGINT, nullable=False, server_default="0"),
    Column("is_infinite", BOOLEAN, nullable=False, server_default="0"),
    UniqueConstraint("user", "arcade", name="paseli_balance_uk"),
    mysql_charset="utf8mb4",
)

campaign_progress: Table = Table(
    "campaign_progress",
    metadata,
    Column("id", BIGINT, nullable=False, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("aime_user.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("campaign_id", INTEGER, ForeignKey("campaign.id", ondelete="cascade", onupdate="cascade"), nullable=False),
    Column("is_participating", INTEGER, nullable=False, server_default="0"),
    Column("progress", INTEGER, nullable=False, server_default="0"),
    UniqueConstraint("campaign_id", "user_id", name="campaign_progress_uk"),
    mysql_charset="utf8mb4",
)

class UserData(BaseData):
    async def create_user(
        self,
        id: Optional[int] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        permission: int = 1,
    ) -> Optional[int]:
        if id is None:
            sql = insert(aime_user).values(
                username=username,
                email=email,
                password=password,
                permissions=permission,
            )
        else:
            sql = insert(aime_user).values(
                id=id,
                username=username,
                email=email,
                password=password,
                permissions=permission,
            )

        conflict = sql.on_duplicate_key_update(
            username=username, email=email, password=password, permissions=permission
        )

        result = await self.execute(conflict)
        if result is None:
            return None
        return result.lastrowid

    async def get_user(self, user_id: int) -> Optional[Row]:
        sql = select(aime_user).where(aime_user.c.id == user_id)
        result = await self.execute(sql)
        if result is None:
            return False
        return result.fetchone()

    async def check_password(self, user_id: int, passwd: bytes = None) -> bool:
        usr = await self.get_user(user_id)
        if usr is None:
            return False

        if usr["password"] is None:
            return False
        
        if passwd is None or not passwd:
            return False

        return bcrypt.checkpw(passwd, usr["password"].encode())

    async def delete_user(self, user_id: int) -> None:
        sql = aime_user.delete(aime_user.c.id == user_id)

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to delete user with id {user_id}")

    async def get_unregistered_users(self) -> List[Row]:
        """
        Returns a list of users who have not registered with the webui. They may or may not have cards.
        """
        sql = select(aime_user).where(aime_user.c.password == None)

        result = await self.execute(sql)
        if result is None:
            return None
        return result.fetchall()

    async def find_user_by_email(self, email: str) -> Row:
        sql = select(aime_user).where(aime_user.c.email == email)
        result = await self.execute(sql)
        if result is None:
            return False
        return result.fetchone()

    async def find_user_by_username(self, username: str) -> List[Row]:
        sql = aime_user.select(aime_user.c.username.like(f"%{username}%"))
        result = await self.execute(sql)
        if result is None:
            return False
        return result.fetchall()

    async def change_password(self, user_id: int, new_passwd: str) -> bool:
        sql = aime_user.update(aime_user.c.id == user_id).values(password = new_passwd)

        result = await self.execute(sql)
        return result is not None

    async def change_username(self, user_id: int, new_name: str) -> bool:
        sql = aime_user.update(aime_user.c.id == user_id).values(username = new_name)

        result = await self.execute(sql)
        return result is not None

    async def get_user_by_username(self, username: str) -> Optional[Row]:
        result = await self.execute(aime_user.select(aime_user.c.username == username))
        if result: return result.fetchone()

    async def change_permission(self, user_id: int, new_perms: int) -> Optional[bool]:
        sql = aime_user.update(aime_user.c.id == user_id).values(permissions = new_perms)

        result = await self.execute(sql)
        return result is not None

    async def change_email(self, user_id: int, new_email: int) -> Optional[bool]:
        sql = aime_user.update(aime_user.c.id == user_id).values(email = new_email)

        result = await self.execute(sql)
        return result is not None
    
    async def get_refid_by_user(self, user_id: int, game: str, ver: int) -> Optional[str]:
        sql = refid.select(and_(refid.c.user == user_id, refid.c.game == game, refid.c.version == ver))

        result = await self.execute(sql)
        if result is None:
            return None
        
        row = result.fetchone()
        if row is not None:
            return row['id']

    async def get_refid_info_by_refid(self, refid_: str) -> Optional[str]:
        result = await self.execute(refid.select(refid.c.id == refid_))
        if result is not None:
            return result.fetchone()
    
    async def get_user_id_by_refid(self, refid_: str) -> Optional[int]:
        sql = refid.select(refid.c.id == refid_)

        result = await self.execute(sql)
        if result is None:
            return None
        
        row = result.fetchone()
        if row is not None:
            return row['user']

    async def create_refid(self, user_id: int, game: str, ver: int) -> Optional[str]:
        refid_ = ''.join(random.choice('0123456789ABCDEF') for _ in range(16))
        sql = insert(refid).values(
            id=refid_,
            user=user_id,
            game=game,
            version=ver
        )

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to insert refid {refid_} for user {user_id} for {game} v{ver}")
            return None
        return refid_
    
    async def set_user_pin(self, user_id: int, pin: str) -> None:
        sql = aime_user.update(aime_user.c.id == user_id).values(
            pin = pin
        )

        result = await self.execute(sql)
        if result is None:
            self.logger.error(f"Failed to set user {user_id} pin to {pin}")

    async def create_paseli_session(self, user_id: int, machine_id: int, game: str) -> Optional[str]:
        sesh_id = ''.join(random.choice('0123456789ABCDEF') for _ in range(16))
        result = await self.execute(insert(paseli_sesh).values(
            id=sesh_id,
            user=user_id,
            machine=machine_id,
            game=game,
        ))

        if result:
            return sesh_id
        
        self.logger.error(f"Failed to create paseli session for user {user_id} on machine {machine_id} {game}")

    async def close_paseli_session(self, sesh_id: str) -> None:
        result = await self.execute(paseli_sesh.update(paseli_sesh.c.id==sesh_id).values(closed=datetime.now()))
        if not result:
            self.logger.error(f"Failed to close paseli session for {sesh_id}")

    async def get_open_paseli_sessions_by_user(self, user_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_sesh.select(and_(paseli_sesh.c.user == user_id, paseli_sesh.c.closed is None)))
        if result:
            return result.fetchall()

    async def get_paseli_sessions_by_user(self, user_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_sesh.select(paseli_sesh.c.user == user_id))
        if result:
            return result.fetchall()

    async def get_paseli_sessions_by_machine(self, machine_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_sesh.select(paseli_sesh.c.machine == machine_id))
        if result:
            return result.fetchall()

    async def get_paseli_sessions_by_user_machine(self, user_id: int, machine_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_sesh.select(and_(paseli_sesh.c.user == user_id, paseli_sesh.c.machine == machine_id)))
        if result:
            return result.fetchall()

    async def get_paseli_session_by_id(self, sesh_id: str) -> Optional[Row]:
        result = await self.execute(paseli_sesh.select(paseli_sesh.c.id == sesh_id))
        if result:
            return result.fetchone()

    async def put_paseli_transaction(self, sesh_id: str, tx_num: int, ammount: int, detail: str, readable: Optional[str] = None) -> Optional[int]:
        sql = insert(paseli_tx).values(
            sesh_id=sesh_id,
            tx_num=tx_num,
            ammount=ammount,
            detail=detail,
            detail_readable=readable,
        )

        result = await self.execute(sql.on_duplicate_key_update(sesh_id=sesh_id))
        if result:
            return result.inserted_primary_key['id']
        
        self.logger.error(f"Failed to create paseli tx for session {sesh_id} for {ammount}p {detail}")

    async def get_paseli_transaction_by_id(self, tx_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_tx.select(paseli_tx.c.id == tx_id))
        if result:
            return result.fetchall()

    async def get_paseli_transactions_by_session(self, sesh_id: str) -> Optional[List[Row]]:
        result = await self.execute(paseli_tx.select(paseli_tx.c.sesh_id == sesh_id))
        if result:
            return result.fetchall()

    async def create_paseli_balance(self, user_id: int, arcade_id: Optional[int], starting_ammount: int = 0) -> Optional[int]:
        sql = insert(paseli_balance).values(
            user = user_id,
            arcade = arcade_id,
            balance = starting_ammount
        )

        conflict = sql.on_duplicate_key_update(user = user_id)

        result = await self.execute(conflict)
        if result:
            return result.inserted_primary_key['id']
        
        self.logger.error(f"Failed to create paseli balance entry for user {user_id} at arcade {arcade_id} with {starting_ammount} starting balance")

    async def add_paseli_balance_by_user_arcade(self, user_id: int, arcade_id: Optional[int], tx_ammount: int):
        result = await self.execute(paseli_balance.update(and_(paseli_balance.c.user == user_id, paseli_balance.c.arcade == arcade_id)).values(
            balance=paseli_balance.c.balance + tx_ammount,
            ammount_added=paseli_balance.c.ammount_added + tx_ammount
        ))

        if not result:
            self.logger.error(f"Failed to add {tx_ammount}p to user {user_id} at arcade {arcade_id}")

    async def add_paseli_balance_by_id(self, bal_id: int, tx_ammount: int):
        result = await self.execute(paseli_balance.update(paseli_balance.c.id == bal_id).values(
            balance=paseli_balance.c.balance + tx_ammount,
            ammount_added=paseli_balance.c.ammount_added + tx_ammount
        ))

        if not result:
            self.logger.error(f"Failed to add {tx_ammount}p to balance {bal_id}")

    async def spend_paseli_balance_by_user_arcade(self, user_id: int, arcade_id: Optional[int], tx_ammount: int):
        result = await self.execute(paseli_balance.update(and_(paseli_balance.c.user == user_id, paseli_balance.c.arcade == arcade_id)).values(
            balance=paseli_balance.c.balance - tx_ammount,
            ammount_spend=paseli_balance.c.ammount_spend + tx_ammount
        ))

        if not result:
            self.logger.error(f"Failed to remove {tx_ammount}p from' user {user_id} at arcade {arcade_id}")

    async def spend_paseli_balance_by_id(self, bal_id: int, tx_ammount: int):
        result = await self.execute(paseli_balance.update(paseli_balance.c.id == bal_id).values(
            balance=paseli_balance.c.balance - tx_ammount,
            ammount_spend=paseli_balance.c.ammount_spend + tx_ammount
        ))

        if not result:
            self.logger.error(f"Failed to remove {tx_ammount}p from balance {bal_id}")

    async def adjust_paseli_balance_by_user_arcade(self, user_id: int, arcade_id: Optional[int], tx_ammount: int):
        result = await self.execute(paseli_balance.update(and_(paseli_balance.c.user == user_id, paseli_balance.c.arcade == arcade_id)).values(
            balance=paseli_balance.c.balance + tx_ammount,
            ammount_adjusted=paseli_balance.c.ammount_adjusted + tx_ammount
        ))

        if not result:
            self.logger.error(f"Failed to adjust {tx_ammount}p from' user {user_id} at arcade {arcade_id}")

    async def adjust_paseli_balance_by_id(self, bal_id: int, tx_ammount: int):
        result = await self.execute(paseli_balance.update(paseli_balance.c.id == bal_id).values(
            balance=paseli_balance.c.balance + tx_ammount,
            ammount_adjusted=paseli_balance.c.ammount_adjusted + tx_ammount
        ))

        if not result:
            self.logger.error(f"Failed to adjust {tx_ammount}p from balance {bal_id}")

    async def get_paseli_balance_by_id(self, bal_id: int) -> Optional[Row]:
        result = await self.execute(paseli_balance.select(paseli_balance.c.id == bal_id))
        if result:
            return result.fetchone()

    async def get_paseli_balance_by_user(self, user_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_balance.select(paseli_balance.c.user == user_id))
        if result:
            return result.fetchall()

    async def get_paseli_balance_by_arcade(self, arcade_id: int) -> Optional[List[Row]]:
        result = await self.execute(paseli_balance.select(paseli_balance.c.arcade == arcade_id))
        if result:
            return result.fetchall()

    async def get_paseli_balance_by_user_arcade(self, user_id: int, arcade_id: Optional[int] = None) -> Optional[Row]:
        result = await self.execute(paseli_balance.select(and_(paseli_balance.c.user == user_id, paseli_balance.c.arcade == arcade_id)))
        if result:
            return result.fetchone()

    async def get_user_campaign_progress_by_campaign(self, user_id: int, campaign_id: int) -> Optional[Row]:
        result = await self.execute(campaign_progress
            .join(campaign, campaign_progress.c.campaign_id == campaign.c.id)
            .select(and_(campaign_progress.c.user_id == user_id, campaign_progress.c.campaign_id == campaign_id)))
        
        if result is not None:
            return result.fetchone()

    async def get_user_all_campaign_progress(self, user_id: int) -> Optional[List[Row]]:
        result = await self.execute(campaign_progress
            .join(campaign, campaign_progress.c.campaign_id == campaign.c.id)
            .select(campaign_progress.c.user_id == user_id))
        
        if result is not None:
            return result.fetchall()

    async def get_user_active_campaign_progress(self, user_id: int) -> Optional[List[Row]]:
        # distrib_end_date instead of end_date to give the games time to distribute the rewards
        result = await self.execute(campaign_progress
            .join(campaign, campaign_progress.c.campaign_id == campaign.c.id)
            .select(and_(campaign_progress.c.user_id == user_id, and_(
                or_(campaign.c.start_date >= datetime.now(), campaign.c.start_date == None),
                or_(campaign.c.distrib_end_date < datetime.now(), campaign.c.distrib_end_date == None),
            ))))
        
        if result is not None:
            return result.fetchall()

    async def get_user_all_campaign_progress_by_game(self, user_id: int, game_id: str) -> Optional[List[Row]]:
        result = await self.execute(campaign_progress
            .join(campaign, campaign_progress.c.campaign_id == campaign.c.id)
            .join(campaign_game, campaign_progress.c.campaign_id == campaign_game.c.campaign_id)
            .select(and_(campaign_progress.c.user_id == user_id, campaign_game.c.game_id == game_id)))
        
        if result is not None:
            return result.fetchall()

    async def get_user_active_campaign_progress_by_game(self, user_id: int, game_id: str) -> Optional[List[Row]]:
        result = await self.execute(campaign_progress
            .join(campaign, campaign_progress.c.campaign_id == campaign.c.id)
            .join(campaign_game, campaign_progress.c.campaign_id == campaign_game.c.campaign_id)
            .select(and_(and_(campaign_progress.c.user_id == user_id, campaign_game.c.game_id == game_id), and_(
                or_(campaign.c.start_date >= datetime.now(), campaign.c.start_date == None),
                or_(campaign.c.distrib_end_date < datetime.now(), campaign.c.distrib_end_date == None),
            ))))
        
        if result is not None:
            return result.fetchall()

    async def set_user_campaign_is_participating(self, user_id: int, campaign_id: int, is_participating: bool) -> Optional[bool]:
        sql = insert(campaign_progress).values(
            user_id = user_id,
            campaign_id = campaign_id,
            is_participating = is_participating
        )

        conflict = sql.on_duplicate_key_update(is_participating = is_participating)
        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to update campaign participation status for user {user_id} on campaign {campaign_id}!")
            return None
        return result.lastrowid

    async def set_user_campaign_progress(self, user_id: int, campaign_id: int, progress: int) -> Optional[bool]:
        sql = insert(campaign_progress).values(
            user_id = user_id,
            campaign_id = campaign_id,
            is_participating = 1,
            progress = progress
        )

        conflict = sql.on_duplicate_key_update(progress = progress)
        result = await self.execute(conflict)
        if result is None:
            self.logger.error(f"Failed to update campaign progress for user {user_id} on campaign {campaign_id} to {progress}!")
            return None
        return result.lastrowid
