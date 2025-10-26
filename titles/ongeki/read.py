import hmac
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, cast

import UnityPy
import yaml
from UnityPy.classes import Texture2D
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.models.mixins import array_element, element

from read import BaseReader
from core.config import CoreConfig

from .config import OngekiConfig
from .const import OngekiConstants
from .database import OngekiData

config = ParserConfig(fail_on_unknown_properties=False)
parser = XmlParser(config=config)


@dataclass
class StringID:
    id: int = field(metadata={"type": "Element", "name": "id"}, default=-1)
    string: str = field(metadata={"type": "Element", "name": "str"}, default="")


@dataclass
class LimitBreakItemStringID:
    value: StringID = field(
        metadata={"type": "Element", "name": "Value"}, default_factory=StringID
    )
    id: int = field(metadata={"type": "Element", "name": "id"}, default=0)
    string: str = field(metadata={"type": "Element", "name": "str"}, default="")


class EventType(Enum):
    NONE = "None"
    ANNOUNCEMENT = "Announcement"
    MOVIE = "Movie"
    ADD_MY_LIST = "AddMyList"
    UNLOCK_CHAPTER = "UnlockChapter"
    JEWEL_EVENT = "JewelEvent"
    RANKING_EVENT = "RankingEvent"
    ACCEPT_RANKING_EVENT = "AcceptRankingEvent"
    UNLOCK_MUSIC = "UnlockMusic"
    UNLOCK_CARD = "UnlockCard"
    UNLOCK_TROPHY = "UnlockTrophy"
    UNLOCK_NAMEPLATE = "UnlockNamePlate"
    UNLOCK_LIMIT_BREAK_ITEM = "UnlockLimitBreakItem"
    MISSION_EVENT = "MissionEvent"
    DAILY_BONUS = "DailyBonus"
    UNLOCK_BOSS_LOCK_EARLY = "UnlockBossLockEarly"
    UNLOCK_PURCHASE_ITEM = "UnlockPurchaseItem"
    TECH_CHALLENGE_EVENT = "TechChallengeEvent"
    ACCEPT_TECH_CHALLENGE_EVENT = "AcceptTechChallengeEvent"
    SILVER_JEWEL_EVENT = "SilverJewelEvent"
    MAP_EVENT = "MapEvent"


@dataclass
class EventBase:
    event_type: EventType = field(
        metadata={"type": "Element", "name": "EventType"},
        default=EventType.NONE,
    )


@dataclass
class EventMissionEvent(EventBase):
    mission_name: StringID = field(
        metadata={"type": "Element", "name": "MissionName"}, default_factory=StringID
    )


@dataclass
class EventData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"}, default="")
    name: StringID = field(
        metadata={"type": "Element", "name": "Name"}, default_factory=StringID
    )
    event_type: EventType = field(
        metadata={"type": "Element", "name": "EventType"},
        default=EventType.NONE,
    )
    event: EventBase = field(
        metadata={"type": "Element", "name": "Event"},
        default_factory=lambda: EventBase(EventType.NONE),
    )


class CardAttribute(Enum):
    FIRE = "Fire"
    AQUA = "Aqua"
    LEAF = "Leaf"
    MAX = "Max"


class CardRarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"
    SR_PLUS = "SRPlus"
    MAX = "Max"


@dataclass
class CardEffect:
    is_effect: bool = element(name="IsEffect", default=False)
    effect_id: int = element(name="EffectID", default=0)


@dataclass
class PersonalityNameStringID:
    string_id: StringID = element(name="StringID", default_factory=StringID)


@dataclass
class PersonalityIDs:
    personality_names: list[PersonalityNameStringID] = array_element(
        name="PersonalityNameStringID"
    )


@dataclass
class LevelParamItem:
    values: list[int] = array_element(name="int")


@dataclass
class CardData:
    data_name: str = element(name="dataName", default="")
    name: StringID = element(name="Name", default_factory=StringID)
    chara_id: StringID = element(name="CharaID", default_factory=StringID)
    nickname: str = element(name="NickName", default="")
    sort_order: int = element(name="SortOrder", default=0)
    attribute: CardAttribute = element(name="Attribute", default=CardAttribute.FIRE)
    school: StringID = element(name="School", default_factory=StringID)
    name_for_common_model: str = element(name="NameForCommonModel", default="")
    is_common_model: bool = element(name="IsCommonModel", default=False)
    is_digital: bool = element(name="IsDigital", default=False)
    is_ticket_usable: bool = element(name="IsTicketUsable", default=False)
    card_effect: CardEffect = element(name="CardEffect", default_factory=CardEffect)
    gakunen: StringID = element(name="Gakunen", default_factory=StringID)
    personality_ids: PersonalityIDs = element(
        name="PersonalityIDs", default_factory=PersonalityIDs
    )
    rarity: CardRarity = element(name="Rarity", default=CardRarity.N)
    level_param: LevelParamItem = element(
        name="LevelParam", default_factory=LevelParamItem
    )
    skill_id: StringID = element(name="SkillID", default_factory=StringID)
    cho_kaika_skill_id: StringID = element(
        name="ChoKaikaSkillID", default_factory=StringID
    )
    card_rights_name: StringID = element(
        name="CardRightsName", default_factory=StringID
    )
    version_id: StringID = element(name="VersionID", default_factory=StringID)
    card_number_string: str = element(name="CardNumberString", default="")
    license_id: StringID = element(name="LicenseID", default_factory=StringID)
    is_locked_at_the_beginning: bool = element(
        name="IsLockedAtTheBeginning", default=False
    )
    print_end_date_time: datetime = element(
        name="PrintEndDateTime",
        format="%Y-%m-%dT%H:%M:%S",
        default_factory=lambda: datetime(1, 1, 1, 0, 0, 0),
    )


@dataclass
class PathName:
    path: str = element(name="path", default="")


@dataclass
class FumenData:
    fumen_const_integer_part: int = element(name="FumenConstIntegerPart", default=0)
    fumen_const_fractional_part: int = element(
        name="FumenConstFractionalPart", default=0
    )
    fumen_file: PathName = element(name="FumenFile", default_factory=PathName)


@dataclass
class FumenDataList:
    charts: list[FumenData] = array_element(name="FumenData")


@dataclass
class WaveAttribute:
    attribute_types: list[CardAttribute] = array_element(name="AttributeType")


@dataclass
class BossLockReward:
    reward_name: StringID = element(name="RewardName", default_factory=StringID)
    reward_count: int = element(name="RewardCount", default=0)


@dataclass
class BossLockRewards:
    rewards: list[BossLockReward] = array_element(name="BossLockReward")


@dataclass
class MusicData:
    data_name: str = element(name="dataName", default="")
    name: StringID = element(name="Name", default_factory=StringID)
    artist_name: StringID = element(name="ArtistName", default_factory=StringID)
    music_rights_name: StringID = element(
        name="MusicRightsName", default_factory=StringID
    )
    music_source_name: StringID = element(
        name="MusicSourceName", default_factory=StringID
    )
    genre: StringID = element(name="Genre", default_factory=StringID)
    first_chapter_name: StringID = element(
        name="FirstChapterName", default_factory=StringID
    )
    fumen_data: FumenDataList = element(name="FumenData", default_factory=FumenDataList)
    is_lunatic: bool = element(name="IsLunatic", default=False)
    is_remaster: bool = element(name="IsReMaster", default=False)
    boss_card: StringID = element(name="BossCard", default_factory=StringID)
    boss_level: int = element(name="BossLevel", default=0)
    wave_attribute: WaveAttribute = element(
        name="WaveAttribute", default_factory=WaveAttribute
    )
    cost_to_unlock: int = element(name="CostToUnlock", default=0)
    finish_bonus: int = element(name="FinishBonus", default=0)
    ep_release_flag: bool = element(name="EpReleaseFlag", default=False)
    version_id: StringID = element(name="VersionID", default_factory=StringID)
    sort_order: int = element(name="SortOrder", default=0)
    stage_id: StringID = element(name="StageID", default_factory=StringID)
    possessing_from_the_beginning: bool = element(
        name="PossessingFromTheBeginning", default=False
    )
    is_locked_at_the_beginning: bool = element(
        name="IsLockedAtTheBeginning", default=False
    )
    release_version: datetime = element(
        name="ReleaseVersion",
        format="%Y-%m-%dT%H:%M:%S",
        default_factory=lambda: datetime(1, 1, 1, 0, 0, 0),
    )
    name_for_sort: str = element(name="NameForSort", default="")
    boss_lock_hp_coef: int = element(name="BossLockHpCoef", default=0)
    boss_lock_rewards: BossLockRewards = element(
        name="BossLockRewards", default_factory=BossLockRewards
    )
    boss_voice_no: int = element(name="BossVoiceNo", default=0)
    is_bonus_track: bool = element(name="IsBonusTrack", default=False)


@dataclass
class Version:
    major: int = element(name="major", default=0)
    minor: int = element(name="minor", default=0)
    release: int = element(name="release", default=0)


@dataclass
class DataConfig:
    version: Version = element(optional=False, name="version")
    card_maker_version: Version = element(optional=False, name="cardMakerVersion")


class ItemType(Enum):
    NONE = "None"
    CARD = "Card"
    NAMEPLATE = "NamePlate"
    TROPHY = "Trophy"
    LIMIT_BREAK_ITEM = "LimitBreakItem"
    ALMIGHTY_JEWEL = "AlmightyJewel"
    MONEY = "Money"
    MUSIC = "Music"
    PROFILE_VOICE = "ProfileVoice"
    PRESENT = "Present"
    CHAPTER_JEWEL = "ChapterJewel"
    GACHA_TICKET = "GachaTicket"
    KAIKA_ITEM = "KaikaItem"
    EXP_UP_ITEM = "ExpUpItem"
    INTIMATE_UP_ITEM = "IntimateUpItem"
    BOOK_ITEM = "BookItem"
    SYSTEM_VOICE = "SystemVoice"
    COSTUME = "Costume"
    MEDAL = "Medal"
    ATTACHMENT = "Attachment"
    UNLOCK_ITEM = "UnlockItem"
    SIZUKU = "Sizuku"
    MAX = "Max"


@dataclass
class RewardItem:
    item_type: ItemType = element(name="ItemType", default=ItemType.NONE)
    item_name: StringID = element(name="ItemName", default=StringID)


@dataclass
class RewardData:
    data_name: str = element(name="dataName", default="")
    name: StringID = element(name="Name", default_factory=StringID)
    item_type: ItemType = element(name="ItemType", default=ItemType.NONE)
    reward_item: RewardItem = element(name="RewardItem", default_factory=RewardItem)


class OngekiReader(BaseReader):
    def __init__(
        self,
        config: CoreConfig,
        version: int,
        bin_dir: Optional[str],
        opt_dir: Optional[str],
        extra: Optional[str],
    ) -> None:
        super().__init__(config, version, bin_dir, opt_dir, extra)
        self.data = OngekiData(config)

        cfg_dir = os.environ["ARTEMIS_CFG_DIR"]
        self.game_cfg = OngekiConfig()

        if os.path.exists(f"{cfg_dir}/{OngekiConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{OngekiConstants.CONFIG_NAME}"))
            )

        try:
            self.logger.info(
                f"Start importer for {OngekiConstants.game_ver_to_string(version)}"
            )
        except IndexError:
            self.logger.error(f"Invalid ongeki version {version}")
            exit(1)

    async def read(self) -> None:
        for img_dir in {"jacket", "card"}:
            if not os.path.exists(f"titles/ongeki/img/{img_dir}"):
                os.makedirs(f"titles/ongeki/img/{img_dir}")

        data_dirs = []
        if self.bin_dir is not None:
            data_dirs += self.get_data_directories(self.bin_dir)

        if self.opt_dir is not None:
            data_dirs += self.get_data_directories(self.opt_dir)

        for dir in data_dirs:
            opt_id = await self.read_opt_info(dir)

            await self.read_events(f"{dir}/event", opt_id)
            await self.read_music(f"{dir}/music", opt_id)
            await self.read_card(f"{dir}/card", opt_id)
            await self.read_reward(f"{dir}/reward", opt_id)
            await self.extract_assets(f"{dir}/assets")

        # terrible hack that's basically
        # - traverse up bin_dir until it hits mu3_Data
        # - traverse down to get the root assets dir, since it's not in A000
        # we have to do this since artemis accepts pretty much anything as
        # bin_dir and opt_dir as long as it has a folder named Axxx
        if self.bin_dir is not None:
            streaming_assets_assets_dir = self.bin_dir

            if "mu3_data" not in streaming_assets_assets_dir.lower():
                # we're given a parent folder of mu3_Data
                for root, dirs, _ in os.walk(streaming_assets_assets_dir):
                    found_mu3_data = False

                    for dir in dirs:
                        if dir.lower() != "mu3_data":
                            continue

                        streaming_assets_assets_dir = os.path.join(root, dir)
                        found_mu3_data = True
                        break

                    if found_mu3_data:
                        break
            else:
                # we're given a child folder of mu3_Data
                while (
                    os.path.basename(
                        os.path.normpath(streaming_assets_assets_dir)
                    ).lower()
                    != "mu3_data"
                ):
                    streaming_assets_assets_dir = os.path.dirname(
                        streaming_assets_assets_dir
                    )

            streaming_assets_assets_dir = os.path.join(
                streaming_assets_assets_dir, "StreamingAssets", "assets"
            )

            await self.extract_assets(streaming_assets_assets_dir)

    async def read_card(self, base_dir: str, opt_id: int | None) -> None:
        self.logger.info(f"Reading cards from {base_dir}...")

        version_ids = {
            1000: OngekiConstants.VER_ONGEKI,
            1005: OngekiConstants.VER_ONGEKI_PLUS,
            1010: OngekiConstants.VER_ONGEKI_SUMMER,
            1015: OngekiConstants.VER_ONGEKI_SUMMER_PLUS,
            1020: OngekiConstants.VER_ONGEKI_RED,
            1025: OngekiConstants.VER_ONGEKI_RED_PLUS,
            1030: OngekiConstants.VER_ONGEKI_BRIGHT,
            1035: OngekiConstants.VER_ONGEKI_BRIGHT_MEMORY,
            1045: OngekiConstants.VER_ONGEKI_BRIGHT_MEMORY,
            1050: OngekiConstants.VER_ONGEKI_REFRESH,
        }

        for root, dirs, files in os.walk(base_dir):
            for dir in dirs:
                if os.path.exists(f"{root}/{dir}/Card.xml"):
                    with open(f"{root}/{dir}/Card.xml", "r", encoding="utf-8") as f:
                        card = parser.from_string(f.read(), clazz=CardData)

                    card_id = card.name.id
                    version = version_ids[card.version_id.id]

                    # skip already existing cards
                    if await self.data.static.get_card(version, card_id) is not None:
                        self.logger.info(f"Card {card_id} already added, skipping")
                        continue

                    rarity = OngekiConstants.RARITY_TYPES[card.rarity.value].value

                    await self.data.static.put_card(
                        version,
                        card_id,
                        opt_id,
                        name=card.name.string,
                        charaId=card.chara_id.id,
                        nickName=card.nickname,
                        school=card.school.string,
                        attribute=card.attribute.value,
                        gakunen=card.gakunen.string,
                        rarity=rarity,
                        levelParam=",".join([str(v) for v in card.level_param.values]),
                        skillId=card.skill_id.id,
                        choKaikaSkillId=card.cho_kaika_skill_id.id,
                        cardNumber=card.card_number_string,
                        imagePath=None,
                    )
                    self.logger.info(f"Added card {card_id}")

    async def read_events(self, base_dir: str, opt_id: int | None) -> None:
        self.logger.info(f"Reading events from {base_dir}...")

        for root, dirs, files in os.walk(base_dir):
            for dir in dirs:
                if os.path.exists(f"{root}/{dir}/Event.xml"):
                    with open(f"{root}/{dir}/Event.xml", "r", encoding="utf-8") as f:
                        event = parser.from_string(f.read(), clazz=EventData)

                    name = event.name.string
                    id = event.name.id
                    event_type = event.event_type.value

                    if isinstance(event.event, EventMissionEvent):
                        name = event.event.mission_name.string

                    await self.data.static.put_event(
                        self.version,
                        id,
                        OngekiConstants.EVT_TYPES[event_type].value,
                        name,
                        opt_id,
                        enabled=False,
                    )
                    self.logger.info(f"Added event {id}")

    async def read_music(self, base_dir: str, opt_id: int | None) -> None:
        self.logger.info(f"Reading music from {base_dir}...")

        for root, dirs, files in os.walk(base_dir):
            for dir in dirs:
                if os.path.exists(f"{root}/{dir}/Music.xml"):
                    with open(f"{root}/{dir}/Music.xml", "r", encoding="utf-8") as f:
                        music = parser.from_string(f.read(), clazz=MusicData)

                    song_id = music.name.id
                    title = music.name.string
                    artist = music.artist_name.string
                    genre = music.genre.string

                    for idx, chart in enumerate(music.fumen_data.charts):
                        chart_path = chart.fumen_file.path

                        if not chart_path or not os.path.exists(
                            f"{root}/{dir}/{chart_path}"
                        ):
                            continue

                        notecount = -1

                        with open(
                            f"{root}/{dir}/{chart_path}",
                            encoding="utf-8",
                            newline="\r\n",
                        ) as f:
                            for line in f:
                                (command, *parameters) = line.split("\t")

                                if command == "T_TOTAL":
                                    notecount = int(parameters[0])
                                    break

                        if notecount == -1:
                            self.logger.error(
                                "%s/%s: invalid chart file: cannot find notecount",
                                dir,
                                chart_path,
                            )
                            continue

                        if idx == 4 and not music.is_lunatic:
                            self.logger.warning(
                                "%s: Found filled-in LUNATIC difficulty, but IsLunatic is false?",
                                music.data_name,
                            )

                        if idx == 4:
                            chart_id = 10  # LUNATIC/Re:MASTER
                        else:
                            chart_id = idx

                        level = (
                            chart.fumen_const_integer_part * 100
                            + chart.fumen_const_fractional_part
                        ) / 100

                        await self.data.static.put_chart(
                            self.version,
                            song_id,
                            chart_id,
                            title,
                            artist,
                            genre,
                            level,
                            notecount,
                            opt_id,
                        )

                        self.logger.info(f"Added song {song_id} chart {chart_id}")

    async def read_reward(self, base_dir: str, opt_id: int | None) -> None:
        self.logger.info(f"Reading rewards from {base_dir}...")

        for root, dirs, files in os.walk(base_dir):
            for dir in dirs:
                if os.path.exists(f"{root}/{dir}/Reward.xml"):
                    with open(f"{root}/{dir}/Reward.xml", "r", encoding="utf-8") as f:
                        reward = parser.from_string(f.read(), clazz=RewardData)

                    rewardId = reward.name.id
                    rewardname = reward.name.string
                    itemKind = OngekiConstants.REWARD_TYPES[
                        reward.item_type.value
                    ].value
                    itemId = reward.reward_item.item_name.id

                    await self.data.static.put_reward(
                        self.version, rewardId, rewardname, itemKind, itemId, opt_id
                    )
                    self.logger.info(f"Added reward {rewardId}")

    async def extract_assets(self, assets_dir: str) -> None:
        if not os.path.exists(assets_dir):
            return

        self.logger.info("Reading assets from %s", assets_dir)

        output = "titles/ongeki/img"
        env = UnityPy.Environment(assets_dir)

        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue

            t: Texture2D = obj.read()
            lower_name = t.m_Name.lower()

            if not lower_name.startswith(("ui_jacket", "ui_card")):
                t.image.close()
                continue

            if lower_name.startswith(("ui_jacket", "ui_card")) and lower_name.endswith(
                "_s"
            ):
                t.image.close()
                continue

            _, asset_type, asset_id = lower_name.split("_", 2)

            if not asset_id.isnumeric():
                self.logger.warning(
                    "Invalid asset ID found for %s: %s", t.m_Name, asset_id
                )
                continue

            self.logger.info("Extracted %s", t.m_Name)

            asset_id = int(asset_id)
            filename = self.obfuscate_filename(f"{t.m_Name}.webp")

            if os.path.exists(f"{output}/{asset_type}/{filename}"):
                continue

            if asset_type == "jacket":
                await self.data.static.set_chart_jacket_path(
                    self.version, asset_id, filename
                )
            if asset_type == "card":
                await self.data.static.set_card_image_path(asset_id, filename)

            t.image.save(
                f"{output}/{asset_type}/{filename}", format="WEBP", quality=85, method=6
            )
            t.image.close()

    def obfuscate_filename(self, filename: str):
        if self.game_cfg.read.asset_hmac_key is None:
            return filename

        asset_hmac_key = self.game_cfg.read.asset_hmac_key.encode("utf-8")
        basename, ext = os.path.splitext(filename)
        basename = hmac.digest(asset_hmac_key, basename.encode("utf-8"), "sha256")[
            :16
        ].hex()

        return f"{basename}{ext}"

    async def read_opt_info(self, opt_dir: str):
        data_config_file = os.path.join(opt_dir, "DataConfig.xml")

        if not os.path.exists(data_config_file):
            self.logger.warning(
                "%s does not contain DataConfig.xml, option info will not be read",
                opt_dir,
            )
            return None

        try:
            with open(data_config_file, "r", encoding="utf-8") as f:
                data_config = parser.from_string(f.read(), clazz=DataConfig)
        except Exception as e:
            self.logger.exception(
                "%s could not be parsed, option info will not be read",
                data_config_file,
                exc_info=e,
            )
            return None

        opt_name = os.path.basename(os.path.normpath(opt_dir))
        opt_row = await self.data.static.get_opt_by_version_folder(
            self.version, opt_name
        )

        if opt_row is None:
            opt_id = await self.data.static.put_opt(
                self.version,
                opt_name,
                data_config.version.release,
                data_config.card_maker_version.release,
            )

            if opt_id is None:
                return None
        else:
            opt_id = cast(int, opt_row.id)

        self.logger.info(
            "option folder %s (database ID %s) contains v%s.%s.%s (cm v%s.%s.%s)",
            opt_name,
            opt_id,
            data_config.version.major,
            data_config.version.minor,
            data_config.version.release,
            data_config.card_maker_version.major,
            data_config.card_maker_version.minor,
            data_config.card_maker_version.release,
        )

        return opt_id
