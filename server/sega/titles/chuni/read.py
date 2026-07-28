import asyncio
import configparser
import hmac
import os
from dataclasses import dataclass, field
from os import path, walk
from pathlib import Path
from typing import Optional, cast

import yaml
from PIL import Image
from xsdata.exceptions import ParserError, XmlContextError
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.models.mixins import array_element, element

from server.sega.config import ArtemisConfig
from read import BaseReader
from server.sega.titles.chuni.config import ChuniConfig
from server.sega.titles.chuni.const import ChuniConstants
from server.sega.titles.chuni.database import ChuniData

config = ParserConfig(fail_on_unknown_properties=False)
parser = XmlParser(config=config)


@dataclass
class StringID:
    id: Optional[int] = field(
        default=None, metadata={"type": "Element", "name": "id", "nillable": True}
    )
    string: Optional[str] = field(
        default=None, metadata={"type": "Element", "name": "str", "nillable": True}
    )
    data: Optional[str] = field(
        default=None, metadata={"type": "Element", "name": "data", "nillable": True}
    )


@dataclass
class ImagePath:
    path: str = field(metadata={"type": "Element", "name": "path"})


@dataclass
class ImagePathOptional:
    path: Optional[str] = field(
        metadata={"type": "Element", "name": "path", "nillable": True}
    )


@dataclass
class StringIDs:
    items: list[StringID] = field(metadata={"type": "Element", "name": "StringID"})


@dataclass
class StringIDList:
    list: StringIDs = field(metadata={"type": "Element", "name": "list"})


@dataclass
class EventSubstance:
    type: int = field(default=0, metadata={"type": "Element", "name": "type"})


@dataclass
class EventData:
    data_name: str = field(default="", metadata={"type": "Element", "name": "dataName"})
    name: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "name"}
    )
    text: Optional[str] = field(
        default=None, metadata={"type": "Element", "name": "text", "nillable": True}
    )
    dds_banner_name: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "ddsBannerName"}
    )
    period_disp_type: int = field(
        default=0, metadata={"type": "Element", "name": "periodDispType"}
    )
    priority: int = field(default=0, metadata={"type": "Element", "name": "priority"})
    substances: EventSubstance = field(
        default_factory=EventSubstance,
        metadata={"type": "Element", "name": "substances"},
    )
    net_open_name: Optional[StringID] = field(
        default=None, metadata={"type": "Element", "name": "netOpenName"}
    )
    always_open: bool = field(
        default=False, metadata={"type": "Element", "name": "alwaysOpen"}
    )
    team_only: bool = field(
        default=False, metadata={"type": "Element", "name": "teamOnly"}
    )
    is_kop: bool = field(default=False, metadata={"type": "Element", "name": "isKop"})


@dataclass
class MusicFumenData:
    type: StringID = field(metadata={"type": "Element", "name": "type"})
    enable: bool = field(metadata={"type": "Element", "name": "enable"})
    file: ImagePathOptional = field(metadata={"type": "Element", "name": "file"})
    level: int = field(metadata={"type": "Element", "name": "level"})
    level_decimal: int = field(metadata={"type": "Element", "name": "levelDecimal"})
    notes_designer: Optional[str] = field(
        metadata={"type": "Element", "name": "notesDesigner", "nillable": True}
    )
    default_bpm: int = field(metadata={"type": "Element", "name": "defaultBpm"})


@dataclass
class MusicFumens:
    fumens: list[MusicFumenData] = field(
        metadata={"type": "Element", "name": "MusicFumenData"}
    )


@dataclass
class MusicData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    release_tag_name: StringID = field(
        metadata={"type": "Element", "name": "releaseTagName"}
    )
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    ex_type: int = field(metadata={"type": "Element", "name": "exType"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    sort_name: str = field(metadata={"type": "Element", "name": "sortName"})
    artist_name: StringID = field(metadata={"type": "Element", "name": "artistName"})
    genre_names: StringIDList = field(
        metadata={"type": "Element", "name": "genreNames"}
    )
    jacket_file: ImagePath = field(metadata={"type": "Element", "name": "jaketFile"})
    first_lock: bool = field(metadata={"type": "Element", "name": "firstLock"})
    priority: int = field(metadata={"type": "Element", "name": "priority"})
    cue_file_name: StringID = field(metadata={"type": "Element", "name": "cueFileName"})
    stage_name: StringID = field(metadata={"type": "Element", "name": "stageName"})
    fumens: MusicFumens = field(metadata={"type": "Element", "name": "fumens"})
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )
    enable_ultima: bool = field(
        metadata={"type": "Element", "name": "enableUltima"}, default=False
    )
    is_gift_music: bool = field(
        metadata={"type": "Element", "name": "isGiftMusic"}, default=False
    )
    release_date: Optional[str] = field(
        metadata={"type": "Element", "name": "releaseDate"}, default=None
    )
    rights_info_name: Optional[StringID] = field(
        metadata={"type": "Element", "name": "rightsInfoName"}, default=None
    )
    music_label_id: Optional[StringID] = field(
        metadata={"type": "Element", "name": "musicLableID"}, default=None
    )
    works_name: Optional[StringID] = field(
        metadata={"type": "Element", "name": "worksName"}, default=None
    )
    label_name: Optional[StringID] = field(
        metadata={"type": "Element", "name": "labelName"}, default=None
    )
    preview_start_time: Optional[int] = field(
        metadata={"type": "Element", "name": "previewStartTime"}, default=None
    )
    preview_end_time: Optional[int] = field(
        metadata={"type": "Element", "name": "previewEndTime"}, default=None
    )
    worlds_end_tag_name: Optional[StringID] = field(
        metadata={"type": "Element", "name": "worldsEndTagName"}, default=None
    )
    star_dif_type: Optional[int] = field(
        metadata={"type": "Element", "name": "starDifType"}, default=None
    )


@dataclass
class NamePlateData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    sort_name: str = field(metadata={"type": "Element", "name": "sortName"})
    image: ImagePath = field(metadata={"type": "Element", "name": "image"})
    default_have: bool = field(metadata={"type": "Element", "name": "defaultHave"})
    explain_text: str = field(metadata={"type": "Element", "name": "explainText"})
    priority: int = field(metadata={"type": "Element", "name": "priority"})
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


@dataclass
class SystemVoiceData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    sort_name: str = field(metadata={"type": "Element", "name": "sortName"})
    cue: StringID = field(metadata={"type": "Element", "name": "cue"})
    image: ImagePath = field(metadata={"type": "Element", "name": "image"})
    default_have: bool = field(metadata={"type": "Element", "name": "defaultHave"})
    explain_text: str = field(metadata={"type": "Element", "name": "explainText"})
    priority: int = field(metadata={"type": "Element", "name": "priority"})
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


@dataclass
class MapIconData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    sort_name: str = field(metadata={"type": "Element", "name": "sortName"})
    image: ImagePath = field(metadata={"type": "Element", "name": "image"})
    default_have: bool = field(metadata={"type": "Element", "name": "defaultHave"})
    explain_text: str = field(metadata={"type": "Element", "name": "explainText"})
    priority: int = field(metadata={"type": "Element", "name": "priority"})
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


@dataclass
class TrophyData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    explain_text: str = field(metadata={"type": "Element", "name": "explainText"})
    default_have: bool = field(metadata={"type": "Element", "name": "defaultHave"})
    rare_type: int = field(metadata={"type": "Element", "name": "rareType"})
    priority: int = field(metadata={"type": "Element", "name": "priority"})
    image: Optional[ImagePathOptional] = field(
        metadata={"type": "Element", "name": "image"}, default=None
    )
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


@dataclass
class CharaData:
    data_name: str = field(default="", metadata={"type": "Element", "name": "dataName"})
    release_tag_name: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "releaseTagName"}
    )
    net_open_name: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "netOpenName"}
    )
    name: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "name"}
    )
    explain_text: Optional[str] = field(
        default=None,
        metadata={"type": "Element", "name": "explainText", "nillable": True},
    )
    sort_name: str = field(default="", metadata={"type": "Element", "name": "sortName"})
    works: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "works"}
    )
    illustrator_name: StringID = field(
        default_factory=StringID,
        metadata={"type": "Element", "name": "illustratorName"},
    )
    default_have: bool = field(
        default=False, metadata={"type": "Element", "name": "defaultHave"}
    )
    rare_type: int = field(default=0, metadata={"type": "Element", "name": "rareType"})
    default_images: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "defaultImages"}
    )
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


@dataclass
class DDSImageData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    dds_file_0: ImagePath = field(metadata={"type": "Element", "name": "ddsFile0"})
    dds_file_1: ImagePath = field(metadata={"type": "Element", "name": "ddsFile1"})
    dds_file_2: ImagePath = field(metadata={"type": "Element", "name": "ddsFile2"})
    net_open_name: Optional[StringID] = field(
        default=None, metadata={"type": "Element", "name": "netOpenName"}
    )


@dataclass
class SkillData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    default_have: bool = field(metadata={"type": "Element", "name": "defaultHave"})
    category: StringID = field(metadata={"type": "Element", "name": "category"})
    info_txt_file: ImagePath = field(
        metadata={"type": "Element", "name": "infoTxtFile"}
    )
    seed_name: Optional[str] = field(
        metadata={"type": "Element", "name": "seedName"}, default=None
    )
    skill_version: Optional[int] = field(
        metadata={"type": "Element", "name": "skillVersion"}, default=None
    )
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


@dataclass
class TicketData:
    data_name: str = field(default="", metadata={"type": "Element", "name": "dataName"})
    name: StringID = field(
        default_factory=StringID, metadata={"type": "Element", "name": "name"}
    )
    type: int = field(default=0, metadata={"type": "Element", "name": "type"})
    target: int = field(default=0, metadata={"type": "Element", "name": "target"})
    explain_text: str = field(
        default="", metadata={"type": "Element", "name": "explainText"}
    )
    stock_max_num: int = field(
        default=0, metadata={"type": "Element", "name": "stockMaxNum"}
    )
    charge_bonus: int = field(
        default=0, metadata={"type": "Element", "name": "chargeBonus"}
    )
    charge_bonus_team: int = field(
        default=0, metadata={"type": "Element", "name": "chargeBonusTeam"}
    )
    charge_bonus_avatar: Optional[int] = field(
        metadata={"type": "Element", "name": "chargeBonusAvatar"}, default=None
    )
    play_reward_point: Optional[int] = field(
        metadata={"type": "Element", "name": "playRewardPoint"}, default=None
    )
    num_charge_credit: Optional[int] = field(
        metadata={"type": "Element", "name": "numChargeCredit"}, default=None
    )
    battle_point_coef_monthly: Optional[int] = field(
        metadata={"type": "Element", "name": "battlePointCoefMonthly"},
        default=None,
    )
    battle_point_coef_emperor: Optional[int] = field(
        metadata={"type": "Element", "name": "battlePointCoefEmperor"},
        default=None,
    )
    add_play_unlock_challenge: Optional[int] = field(
        metadata={"type": "Element", "name": "addPlayUnlockChallenge"},
        default=None,
    )


@dataclass
class LoginBonusDataInfo:
    login_bonus_name: StringID = element(optional=False, name="loginBonusName")


@dataclass
class LoginBonusDataInfoList:
    items: list[LoginBonusDataInfo] = array_element(name="LoginBonusDataInfo")


@dataclass
class LoginBonusPresetData:
    name: StringID = element(optional=False, name="name")
    data_name: str = element(name="dataName", default="")
    disable_flag: bool = element(name="disableFlag", default=False)
    infos: LoginBonusDataInfoList = element(
        name="infos", default_factory=LoginBonusDataInfoList
    )


@dataclass
class LoginBonusData:
    name: StringID = element(optional=False, name="name")
    present: StringID = element(optional=False, name="present")
    item_num: int = element(optional=False, name="itemNum")
    need_login_day_count: int = element(optional=False, name="needLoginDayCount")
    login_bonus_category_type: int = element(
        optional=False, name="loginBonusCategoryType"
    )
    data_name: str = element(name="dataName", default="")
    disable_flag: bool = element(name="disableFlag", default=False)


@dataclass
class ChargeItemSubstanceDummy:
    dummy: int = element(name="dummy", default=0)


@dataclass
class ChargeItemSubstanceTicket:
    ticket_name: StringID = element(name="ticketName", default_factory=StringID)


@dataclass
class ChargeItemSubstance:
    type: int = element(optional=False, name="type")
    dummy: ChargeItemSubstanceDummy = element(
        name="dummy", default_factory=ChargeItemSubstanceDummy
    )
    ticket: ChargeItemSubstanceTicket = element(
        name="ticket", default_factory=ChargeItemSubstanceTicket
    )


@dataclass
class ChargeItemData:
    name: StringID = element(optional=False, name="name")
    type: int = element(optional=False, name="type")
    expiration_days: int = element(optional=False, name="expirationDays")
    consume_type: int = element(optional=False, name="consumeType")
    force_use: bool = element(optional=False, name="forceUse")
    selling_appeal: bool = element(optional=False, name="sellingAppeal")
    data_name: str = element(name="dataName", default="")
    timetable_name: StringID = element(name="timeTableName", default_factory=StringID)
    substances: ChargeItemSubstance = element(
        name="substances", default_factory=ChargeItemSubstance
    )


@dataclass
class AvatarAccessoryData:
    name: StringID = element(optional=False, name="name")
    category: int = element(optional=False, name="category")
    image: ImagePath = element(optional=False, name="image")
    texture: ImagePath = element(optional=False, name="texture")
    data_name: str = element(name="dataName", default="")
    net_open_name: StringID = element(name="netOpenName", default_factory=StringID)
    disable_flag: bool = element(name="disableFlag", default=False)
    sort_name: str = element(name="sortName", default="")
    default_have: bool = element(name="defaultHave", default=False)
    explain_text: str = element(name="explainText", default="")
    priority: int = element(name="priority", default=0)


@dataclass
class StageData:
    data_name: str = field(metadata={"type": "Element", "name": "dataName"})
    net_open_name: StringID = field(metadata={"type": "Element", "name": "netOpenName"})
    release_tag_name: StringID = field(
        metadata={"type": "Element", "name": "releaseTagName"}
    )
    name: StringID = field(metadata={"type": "Element", "name": "name"})
    notes_field_line: StringID = field(
        metadata={"type": "Element", "name": "notesFieldLine"}
    )
    notes_field_file: ImagePath = field(
        metadata={"type": "Element", "name": "notesFieldFile"}
    )
    base_file: ImagePath = field(metadata={"type": "Element", "name": "baseFile"})
    object_file: ImagePathOptional = field(
        metadata={"type": "Element", "name": "objectFile"}
    )
    default_have: bool = field(metadata={"type": "Element", "name": "defaultHave"})
    image: ImagePath = field(metadata={"type": "Element", "name": "image"})
    enable_plate: bool = field(metadata={"type": "Element", "name": "enablePlate"})
    sort_name: Optional[str] = field(
        metadata={"type": "Element", "name": "sortName", "nillable": True}
    )
    priority: int = field(metadata={"type": "Element", "name": "priority"})
    disable_flag: bool = field(
        default=False, metadata={"type": "Element", "name": "disableFlag"}
    )


class ChuniReader(BaseReader):
    def __init__(
        self,
        config: ArtemisConfig,
        version: int,
        bin_dir: Optional[str],
        opt_dir: Optional[str],
        extra: Optional[str],
    ) -> None:
        super().__init__(config, version, bin_dir, opt_dir, extra)
        self.data = ChuniData(config)

        cfg_dir = os.environ["ARTEMIS_CFG_DIR"]
        self.game_cfg = ChuniConfig()

        if path.exists(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"))
            )

        self.dds_images: dict[str, tuple[Path, DDSImageData]] = {}

        try:
            self.logger.info(
                f"Start importer for {ChuniConstants.game_ver_to_string(version)}"
            )
        except IndexError:
            self.logger.error(f"Invalid chunithm version {version}")
            exit(1)

    async def read(self) -> None:
        data_dirs = []
        if self.bin_dir is not None:
            data_dirs += self.get_data_directories(self.bin_dir)

        if self.opt_dir is not None:
            data_dirs += self.get_data_directories(self.opt_dir)

        we_diff = 4
        if self.version >= ChuniConstants.VER_CHUNITHM_NEW:
            we_diff = 5

        for img_dir in {
            "avatar",
            "jacket",
            "nameplate",
            "system_voice_thumbnails",
            "map_icon",
            "trophy",
            "characters",
            "ticket",
            "stage",
        }:
            if not os.path.exists(f"server/sega/titles/chuni/assets/img/{img_dir}"):
                os.makedirs(f"server/sega/titles/chuni/assets/img/{img_dir}")

        for dir in data_dirs:
            self.logger.info("Reading DDSImage from %s", dir)

            for root, dirs, files in os.walk(os.path.join(dir, "ddsImage")):
                for dir in dirs:
                    dds_image_path = Path(root) / dir / "DDSImage.xml"

                    if not dds_image_path.is_file():
                        continue

                    try:
                        dds_image_xml = parser.from_path(dds_image_path, DDSImageData)
                    except (ParserError, TypeError) as e:
                        self.logger.warning(
                            "Failed to parse %s", dds_image_path, exc_info=e
                        )
                        continue

                    self.dds_images[dir] = (dds_image_path, dds_image_xml)

        for dir in data_dirs:
            self.logger.info("Read from %s", dir)

            async with self.data.session.begin():  # pyright: ignore[reportGeneralTypeIssues]
                opt_id = await self.read_opt_info(dir)

                await self.read_events(f"{dir}/event", opt_id)
                await self.read_music(f"{dir}/music", we_diff, opt_id)
                await self.read_charges(f"{dir}/chargeItem", opt_id)
                await self.read_avatar(f"{dir}/avatarAccessory", opt_id)
                await self.read_login_bonus(f"{dir}/", opt_id)
                await self.read_nameplate(f"{dir}/namePlate", opt_id)
                await self.read_system_voice(f"{dir}/systemVoice", opt_id)
                await self.read_map_icon(f"{dir}/mapIcon", opt_id)
                await self.read_trophy(f"{dir}/trophy", opt_id)
                await self.read_character(f"{dir}/chara", opt_id)
                await self.read_ticket(f"{dir}/ticket", opt_id)
                await self.read_skill(f"{dir}/skill", opt_id)

                if self.version >= ChuniConstants.VER_CHUNITHM_X_VERSE:
                    await self.read_stages(f"{dir}/stage", opt_id)

    async def read_login_bonus(self, root_dir: str, opt_id: int | None) -> None:
        for root, dirs, files in walk(f"{root_dir}loginBonusPreset"):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/LoginBonusPreset.xml"):
                    with open(
                        f"{root}/{dir}/LoginBonusPreset.xml", "r", encoding="utf-8"
                    ) as fp:
                        preset = parser.from_string(
                            fp.read(), clazz=LoginBonusPresetData
                        )

                    id = preset.name.id
                    name = preset.name.string
                    is_enabled = not preset.disable_flag

                    if id is None or name is None:
                        self.logger.warning(
                            "Login bonus preset %s does not have a name", dir
                        )
                        continue

                    result = await self.data.static.put_login_bonus_preset(
                        self.version, id, name, is_enabled, opt_id
                    )

                    if result is not None:
                        self.logger.info(f"Inserted login bonus preset {id}")
                    else:
                        self.logger.warning(f"Failed to insert login bonus preset {id}")

                    for idx, bonus in enumerate(preset.infos.items):
                        bonus_id = bonus.login_bonus_name.id
                        bonus_name = bonus.login_bonus_name.string

                        if bonus_id is None or bonus_name is None:
                            self.logger.warning(
                                "Login bonus preset %s, info index %s does not have a name",
                                dir,
                                idx,
                            )
                            continue

                        if not path.exists(
                            f"{root_dir}/loginBonus/loginBonus{bonus_id}/LoginBonus.xml"
                        ):
                            continue

                        with open(
                            f"{root_dir}/loginBonus/loginBonus{bonus_id}/LoginBonus.xml",
                            "r",
                            encoding="utf-8",
                        ) as fp:
                            bonus = parser.from_string(fp.read(), clazz=LoginBonusData)
                            present_id = bonus.present.id
                            present_name = bonus.present.string
                            item_num = bonus.item_num
                            need_login_day_count = bonus.need_login_day_count
                            login_bonus_category_type = bonus.login_bonus_category_type

                            if present_id is None or present_name is None:
                                self.logger.warning(
                                    "Present of login bonus %s is missing", bonus_id
                                )
                                continue

                            result = await self.data.static.put_login_bonus(
                                self.version,
                                id,
                                bonus_id,
                                bonus_name,
                                present_id,
                                present_name,
                                item_num,
                                need_login_day_count,
                                login_bonus_category_type,
                                opt_id,
                            )

                            if result is not None:
                                self.logger.info(f"Inserted login bonus {bonus_id}")
                            else:
                                self.logger.warning(
                                    f"Failed to insert login bonus {bonus_id}"
                                )

    async def read_events(self, evt_dir: str, opt_id: int | None) -> None:
        for root, dirs, files in walk(evt_dir):
            for dir in dirs:
                if not path.exists(f"{root}/{dir}/Event.xml"):
                    continue

                try:
                    event = parser.from_path(Path(root) / dir / "Event.xml", EventData)
                except (ParserError, TypeError) as e:
                    self.logger.warning(f"Failed to parse {dir}/Event.xml", exc_info=e)
                    continue

                if event.name.id is None or event.name.string is None:
                    self.logger.warning(f"{dir}/Event.xml does not contain a name")
                    continue

                result = await self.data.static.put_event(
                    self.version,
                    event.name.id,
                    event.substances.type,
                    event.name.string,
                    opt_id,
                )

                if result is not None:
                    self.logger.info("Inserted event %s", event.name.id)
                else:
                    self.logger.warning("Failed to insert event %s", event.name.id)

        if opt_id is not None:
            await self.data.static.disable_old_announcement_events(self.version, opt_id)

    async def read_music(
        self, music_dir: str, we_diff: int, opt_id: int | None
    ) -> None:
        jacket_assets_dir = Path("server/sega/titles/chuni/assets/img/jacket")
        for root, dirs, files in walk(music_dir):
            for dir in dirs:
                if not path.exists(f"{root}/{dir}/Music.xml"):
                    continue

                try:
                    music = parser.from_path(Path(root) / dir / "Music.xml", MusicData)
                except (ParserError, TypeError, XmlContextError) as e:
                    self.logger.warning(f"Failed to parse {dir}/Music.xml", exc_info=e)
                    continue

                if music.name.id is None or music.name.string is None:
                    self.logger.warning(f"{dir}/Music.xml does not contain a name")
                    continue

                if music.jacket_file.path is not None:
                    jacket_path = (
                        jacket_assets_dir
                        / await asyncio.to_thread(
                            self.obfuscate_filename, music.jacket_file.path
                        )
                    ).with_suffix(".webp")

                    await asyncio.to_thread(
                        self.copy_image,
                        os.path.join(root, dir, music.jacket_file.path),
                        jacket_path,
                    )
                else:
                    jacket_path = None

                if len(music.genre_names.list.items) > 0:
                    genre = music.genre_names.list.items[0].string
                else:
                    genre = None

                for chart in music.fumens.fumens:
                    if not chart.enable:
                        continue

                    if chart.type.id is None:
                        self.logger.warning(f"{dir}/Music.xml is missing a chart ID")
                        continue

                    if chart.type.id == we_diff:
                        if (
                            music.star_dif_type is None
                            or music.worlds_end_tag_name is None
                            or music.worlds_end_tag_name.string is None
                        ):
                            self.logger.warning(
                                f"{dir}/Music.xml has an enabled WORLD'S END chart, but starDifType/worldsEndTagName is null."
                            )
                            continue

                        level = float(music.star_dif_type)
                        we_tag = music.worlds_end_tag_name.string
                    else:
                        level = float(f"{chart.level}.{chart.level_decimal}")
                        we_tag = None

                    result = await self.data.static.put_music(
                        self.version,
                        music.name.id,
                        chart.type.id,
                        music.name.string,
                        music.artist_name.string,
                        level,
                        genre,
                        jacket_path.name if jacket_path is not None else None,
                        we_tag,
                        opt_id,
                    )

                    if result is not None:
                        self.logger.info(
                            f"Inserted music {music.name.id} chart {chart.type.id}"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to insert music {music.name.id} chart {chart.type.id}"
                        )

    async def read_charges(self, charge_dir: str, opt_id: int | None) -> None:
        for root, dirs, files in walk(charge_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/ChargeItem.xml"):
                    with open(
                        f"{root}/{dir}/ChargeItem.xml", "r", encoding="utf-8"
                    ) as fp:
                        charge = parser.from_string(fp.read(), clazz=ChargeItemData)

                    id = charge.name.id
                    name = charge.name.string
                    expirationDays = charge.expiration_days
                    consumeType = charge.consume_type
                    sellingAppeal = charge.selling_appeal

                    if id is None or name is None:
                        self.logger.warning(
                            "%s/ChargeItem.xml does not contain a name", dir
                        )
                        continue

                    result = await self.data.static.put_charge(
                        self.version,
                        id,
                        name,
                        expirationDays,
                        consumeType,
                        sellingAppeal,
                        opt_id,
                    )

                    if result is not None:
                        self.logger.info(f"Inserted charge {id}")
                    else:
                        self.logger.warning(f"Failed to insert charge {id}")

    async def read_avatar(self, avatar_dir: str, opt_id: int | None) -> None:
        avatar_assets_path = Path("server/sega/titles/chuni/assets/img/avatar")

        for root, dirs, files in walk(avatar_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/AvatarAccessory.xml"):
                    with open(
                        f"{root}/{dir}/AvatarAccessory.xml", "r", encoding="utf-8"
                    ) as fp:
                        accessory = parser.from_string(
                            fp.read(), clazz=AvatarAccessoryData
                        )

                    id = accessory.name.id
                    name = accessory.name.string

                    if id is None or name is None:
                        self.logger.warning(
                            "%s/AvatarAccessory.xml is missing a name", dir
                        )
                        continue

                    category = accessory.category

                    original_icon_path = accessory.image.path
                    icon_path = (
                        avatar_assets_path
                        / await asyncio.to_thread(
                            self.obfuscate_filename, original_icon_path
                        )
                    ).with_suffix(".webp")

                    # Resize avatar image to 50% of its original dimensions
                    await asyncio.to_thread(
                        self.copy_image,
                        os.path.join(root, dir, original_icon_path),
                        icon_path,
                        resize_percent=0.5,
                    )

                    original_texture_path = accessory.texture.path
                    texture_path = (
                        avatar_assets_path
                        / await asyncio.to_thread(
                            self.obfuscate_filename, original_texture_path
                        )
                    ).with_suffix(".webp")

                    # Resize texture to 50% of its original dimensions
                    await asyncio.to_thread(
                        self.copy_image,
                        os.path.join(root, dir, original_texture_path),
                        texture_path,
                        resize_percent=0.5,
                    )

                    result = await self.data.static.put_avatar(
                        self.version,
                        id,
                        name,
                        category,
                        icon_path.name,
                        texture_path.name,
                        opt_id,
                    )

                    if result is not None:
                        self.logger.info(f"Inserted avatarAccessory {id}")
                    else:
                        self.logger.warning(f"Failed to insert avatarAccessory {id}")

    async def read_nameplate(self, nameplate_dir: str, opt_id: int | None):
        if not os.path.isdir(nameplate_dir):
            return

        nameplate_assets_dir = Path("server/sega/titles/chuni/assets/img/nameplate")

        for nameplate in os.listdir(nameplate_dir):
            if not os.path.isdir(os.path.join(nameplate_dir, nameplate)):
                continue

            nameplate_xml_path = Path(nameplate_dir) / nameplate / "NamePlate.xml"

            try:
                nameplate_xml = parser.from_path(nameplate_xml_path, NamePlateData)
            except (ParserError, TypeError) as e:
                self.logger.warning(
                    f"Failed to parse {nameplate}/NamePlate.xml", exc_info=e
                )
                continue

            if not nameplate_xml.image.path:
                self.logger.warning(
                    f"{nameplate}/NamePlate.xml does not contain an image path"
                )
                continue

            if nameplate_xml.name.id is None or nameplate_xml.name.string is None:
                self.logger.warning(
                    f"{nameplate}/NamePlate.xml does not contain a name"
                )
                continue

            image_path = (
                nameplate_assets_dir
                / await asyncio.to_thread(
                    self.obfuscate_filename, nameplate_xml.image.path
                )
            ).with_suffix(".webp")

            await self.data.cozynet.put_nameplate(
                version=self.version,
                nameplate_id=nameplate_xml.name.id,
                name=nameplate_xml.name.string,
                sort_name=nameplate_xml.sort_name,
                explain_text=nameplate_xml.explain_text,
                image_path=image_path.name,
                opt_id=opt_id,
            )

            self.logger.info("Inserted nameplate %s", nameplate_xml.name.id)

            await asyncio.to_thread(
                self.copy_image,
                os.path.join(nameplate_dir, nameplate, nameplate_xml.image.path),
                image_path,
            )

            self.logger.info("Converted nameplate %s", nameplate_xml.name.id)

    async def read_system_voice(self, system_voice_dir: str, opt_id: int | None):
        if not os.path.isdir(system_voice_dir):
            return

        thumbnail_assets_dir = Path("server/sega/titles/chuni/assets/img/system_voice_thumbnails")

        for system_voice in os.listdir(system_voice_dir):
            if not os.path.isdir(os.path.join(system_voice_dir, system_voice)):
                continue

            system_voice_xml_path = (
                Path(system_voice_dir) / system_voice / "SystemVoice.xml"
            )

            try:
                system_voice_xml = parser.from_path(
                    system_voice_xml_path, SystemVoiceData
                )
            except (ParserError, TypeError) as e:
                self.logger.warning(
                    f"Failed to parse {system_voice}/SystemVoice.xml", exc_info=e
                )
                continue

            if not system_voice_xml.image.path:
                self.logger.warning(
                    f"{system_voice}/SystemVoice.xml does not contain an image path"
                )
                continue

            if system_voice_xml.name.id is None or system_voice_xml.name.string is None:
                self.logger.warning(
                    f"{system_voice}/SystemVoice.xml does not contain a name"
                )
                continue

            image_path = (
                thumbnail_assets_dir
                / await asyncio.to_thread(
                    self.obfuscate_filename, system_voice_xml.image.path
                )
            ).with_suffix(".webp")

            await self.data.cozynet.put_system_voice(
                version=self.version,
                system_voice_id=system_voice_xml.name.id,
                name=system_voice_xml.name.string,
                explain_text=system_voice_xml.explain_text,
                image_path=image_path.name,
                opt_id=opt_id,
            )

            self.logger.info("Inserted system voice %s", system_voice_xml.name.id)

            await asyncio.to_thread(
                self.copy_image,
                os.path.join(
                    system_voice_dir, system_voice, system_voice_xml.image.path
                ),
                image_path,
            )

            self.logger.info("Converted system voice %s", system_voice_xml.name.id)

    async def read_map_icon(self, map_icon_dir: str, opt_id: int | None):
        if not os.path.isdir(map_icon_dir):
            return

        map_icon_assets_dir = Path("server/sega/titles/chuni/assets/img/map_icon")

        for map_icon in os.listdir(map_icon_dir):
            if not os.path.isdir(os.path.join(map_icon_dir, map_icon)):
                continue

            map_icon_xml_path = Path(map_icon_dir) / map_icon / "MapIcon.xml"

            try:
                map_icon_xml = parser.from_path(map_icon_xml_path, MapIconData)
            except (ParserError, TypeError) as e:
                self.logger.warning(
                    f"Failed to parse {map_icon}/MapIcon.xml", exc_info=e
                )
                continue

            if not map_icon_xml.image.path:
                self.logger.warning(
                    f"{map_icon}/MapIcon.xml does not contain an image path"
                )
                continue

            if map_icon_xml.name.id is None or map_icon_xml.name.string is None:
                self.logger.warning(f"{map_icon}/MapIcon.xml does not contain a name")
                continue

            image_path = (
                map_icon_assets_dir
                / await asyncio.to_thread(
                    self.obfuscate_filename, map_icon_xml.image.path
                )
            ).with_suffix(".webp")

            await self.data.cozynet.put_map_icon(
                version=self.version,
                map_icon_id=map_icon_xml.name.id,
                name=map_icon_xml.name.string,
                sort_name=map_icon_xml.sort_name,
                explain_text=map_icon_xml.explain_text,
                image_path=image_path.name,
                opt_id=opt_id,
            )

            self.logger.info("Inserted map icon %s", map_icon_xml.name.id)

            await asyncio.to_thread(
                self.copy_image,
                os.path.join(map_icon_dir, map_icon, map_icon_xml.image.path),
                image_path,
            )

            self.logger.info("Converted map icon %s", map_icon_xml.name.id)

    async def read_trophy(self, trophy_dir: str, opt_id: int | None):
        if not os.path.isdir(trophy_dir):
            return

        for trophy in os.listdir(trophy_dir):
            if not os.path.isdir(os.path.join(trophy_dir, trophy)):
                continue

            trophy_xml_path = Path(trophy_dir) / trophy / "Trophy.xml"

            try:
                trophy_xml = parser.from_path(trophy_xml_path, TrophyData)
            except (ParserError, TypeError) as e:
                self.logger.warning(f"Failed to parse {trophy}/Trophy.xml", exc_info=e)
                continue

            if trophy_xml.name.id is None or trophy_xml.name.string is None:
                self.logger.warning(f"{trophy}/Trophy.xml does not contain a name")
                continue

            if trophy_xml.image is not None and trophy_xml.image.path is not None:
                original_image_path = trophy_xml.image.path
                image_path = await asyncio.to_thread(
                    self.obfuscate_filename, trophy_xml.image.path
                )
                image_path = os.path.splitext(image_path)[0] + ".webp"
            else:
                original_image_path = None
                image_path = None

            await self.data.cozynet.put_trophy(
                version=self.version,
                trophy_id=trophy_xml.name.id,
                name=trophy_xml.name.string,
                explain_text=trophy_xml.explain_text,
                rare_type=trophy_xml.rare_type,
                image_path=image_path,
                opt_id=opt_id,
            )

            self.logger.info("Inserted trophy %s", trophy_xml.name.id)

            if original_image_path is not None and image_path is not None:
                with Image.open(
                    os.path.join(trophy_dir, trophy, original_image_path)
                ) as img:
                    height = img.width * 72 // 608
                    trophy_img = img.crop((0, 0, img.width, height))
                    trophy_img.save(
                        f"server/sega/titles/chuni/assets/img/trophy/{image_path}",
                        "WEBP",
                        quality=85,
                        method=6,
                    )

                self.logger.info("Converted trophy %s", trophy_xml.name.id)

    async def read_character(self, chara_dir: str, opt_id: int | None):
        if not os.path.isdir(chara_dir):
            return

        character_assets_dir = Path("server/sega/titles/chuni/assets/img/characters")

        for character in os.listdir(chara_dir):
            if not os.path.isdir(os.path.join(chara_dir, character)):
                continue

            chara_xml_path = Path(chara_dir) / character / "Chara.xml"

            try:
                chara_xml = parser.from_path(chara_xml_path, CharaData)
            except (ParserError, TypeError) as e:
                self.logger.warning(
                    f"Failed to parse {character}/Chara.xml", exc_info=e
                )
                continue

            if chara_xml.name.id is None or chara_xml.name.string is None:
                self.logger.warning(f"{character}/Chara.xml does not contain a name")
                continue

            if chara_xml.default_images.id is None:
                self.logger.warning(
                    f"{character}/Chara.xml does not contain a default image"
                )
                continue

            try:
                dds_image_path, dds_image_xml = self.dds_images[
                    f"ddsImage{chara_xml.default_images.id:06}"
                ]
            except KeyError:
                self.logger.warning(
                    "No ddsImage data found for ID %s", chara_xml.default_images.id
                )
                continue

            if not dds_image_xml.dds_file_1.path:
                self.logger.warning(
                    f"ddsImage{chara_xml.default_images.id:06}/DDSImage.xml does not contain a DDS file"
                )
                continue

            image_path = (
                character_assets_dir
                / self.obfuscate_filename(dds_image_xml.dds_file_1.path)
            ).with_suffix(".webp")

            await self.data.cozynet.put_character(
                version=self.version,
                character_id=chara_xml.name.id,
                name=chara_xml.name.string,
                sort_name=chara_xml.sort_name,
                rare_type=chara_xml.rare_type,
                works=chara_xml.works.string,
                illustrator_name=chara_xml.illustrator_name.string,
                image_path=image_path.name,
                opt_id=opt_id,
            )

            self.logger.info("Inserted character %s", chara_xml.name.id)

            await asyncio.to_thread(
                self.copy_image,
                dds_image_path.parent / dds_image_xml.dds_file_1.path,
                image_path,
            )

            self.logger.info("Converted character %s", chara_xml.name.id)

    async def read_ticket(self, ticket_dir: str, opt_id: int | None):
        if not os.path.isdir(ticket_dir):
            return

        ticket_assets_dir = Path("server/sega/titles/chuni/assets/img/ticket")

        for ticket in os.listdir(ticket_dir):
            if not os.path.isdir(os.path.join(ticket_dir, ticket)):
                continue

            ticket_xml_path = Path(ticket_dir) / ticket / "Ticket.xml"

            try:
                ticket_xml = parser.from_path(ticket_xml_path, TicketData)
            except (ParserError, TypeError) as e:
                self.logger.warning(f"Failed to parse {ticket}/Ticket.xml", exc_info=e)
                continue

            if ticket_xml.name.id is None or ticket_xml.name.string is None:
                self.logger.warning(f"{ticket}/Ticket.xml does not contain a name")
                continue

            ticket_id = ticket_xml.name.id
            original_image_path = f"ticket{ticket_id:08}.webp"
            image_path = ticket_assets_dir / await asyncio.to_thread(
                self.obfuscate_filename, original_image_path
            )

            await self.data.cozynet.put_ticket(
                version=self.version,
                ticket_id=ticket_xml.name.id,
                name=ticket_xml.name.string,
                type=ticket_xml.type,
                target=ticket_xml.target,
                stock_max_num=ticket_xml.stock_max_num,
                explain_text=ticket_xml.explain_text,
                image_path=image_path.name,
                opt_id=opt_id,
            )

            self.logger.info("Inserted ticket %s", ticket_xml.name.id)

            await asyncio.to_thread(
                self.copy_image,
                os.path.join(ticket_dir, ticket, original_image_path),
                image_path,
            )

            self.logger.info("Converted ticket %s", ticket_xml.name.id)

    async def read_skill(self, skill_dir: str, opt_id: int | None):
        if not os.path.isdir(skill_dir):
            return

        for skill in os.listdir(skill_dir):
            if not os.path.isdir(os.path.join(skill_dir, skill)):
                continue

            skill_xml_path = Path(skill_dir) / skill / "Skill.xml"

            try:
                skill_xml = parser.from_path(skill_xml_path, SkillData)
            except (ParserError, TypeError) as e:
                self.logger.warning(f"Failed to parse {skill}/Skill.xml", exc_info=e)
                continue

            if skill_xml.name.id is None or skill_xml.name.string is None:
                self.logger.warning(f"{skill}/Skill.xml does not contain a name")
                continue

            if skill_xml.category.id is None or skill_xml.category.string is None:
                self.logger.warning(f"{skill}/Skill.xml does not contain a category")
                continue

            await self.data.cozynet.put_skill(
                version=self.version,
                skill_id=skill_xml.name.id,
                name=skill_xml.name.string,
                skill_version=skill_xml.skill_version,
                category_id=skill_xml.category.id,
                category_name=skill_xml.category.string,
                opt_id=opt_id,
            )

            self.logger.info("Inserted skill %s", skill_xml.name.id)

    async def read_stages(self, stage_dir: str, opt_id: int | None):
        if not os.path.isdir(stage_dir):
            return

        stage_assets_dir = Path("server/sega/titles/chuni/assets/img/stage")

        for stage in os.listdir(stage_dir):
            if not os.path.isdir(os.path.join(stage_dir, stage)):
                continue

            stage_xml_path = Path(stage_dir) / stage / "Stage.xml"

            try:
                stage_xml = parser.from_path(stage_xml_path, StageData)
            except (ParserError, TypeError) as e:
                self.logger.warning("Failed to parse %s/Stage.xml", stage, exc_info=e)
                continue

            if stage_xml.name.id is None or stage_xml.name.string is None:
                self.logger.warning("%s/Stage.xml does not contain a name", stage)
                continue

            if stage_xml.image.path:
                image_path = (
                    stage_assets_dir
                    / await asyncio.to_thread(
                        self.obfuscate_filename, stage_xml.image.path
                    )
                ).with_suffix(".webp")

                await asyncio.to_thread(
                    self.copy_image,
                    os.path.join(stage_dir, stage, stage_xml.image.path),
                    image_path,
                )
                self.logger.info("Converted stage %s", stage_xml.name.id)
            else:
                image_path = None

            await self.data.cozynet.put_stage(
                version=self.version,
                stage_id=stage_xml.name.id,
                name=stage_xml.name.string,
                image_path=image_path.name if image_path is not None else None,
                opt_id=opt_id,
            )

            self.logger.info("Inserted stage %s", stage_xml.name.id)

    def copy_image(
        self,
        src_path: str | Path,
        dst_path: str | Path,
        resize_percent: float | None = None,
    ) -> None:
        # Convert the image to webp and resize it if necessary for easier display on the frontend
        if isinstance(src_path, str):
            src_path = Path(src_path)

        if isinstance(dst_path, str):
            dst_path = Path(dst_path)

        if dst_path.suffix != ".webp":
            dst_path = dst_path.with_suffix(".webp")

        if src_path.is_file() and not dst_path.exists():
            try:
                with Image.open(src_path) as img:
                    if resize_percent:
                        img = img.resize(
                            (
                                int(img.width * resize_percent),
                                int(img.height * resize_percent),
                            )
                        )
                    img.save(dst_path, "WEBP", quality=85, method=6)
            except Exception as e:
                self.logger.warning(
                    f"Failed to convert {src_path.name} to WEBP", exc_info=e
                )

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
        data_conf_file = os.path.join(opt_dir, "data.conf")

        if not os.path.exists(data_conf_file):
            self.logger.warning(
                "%s does not contain data.conf, option info will not be read",
                opt_dir,
            )
            return None

        conf = configparser.ConfigParser()
        conf.read(data_conf_file, "utf-8")

        try:
            ver_major = conf.getint("Version", "VerMajor")
            ver_minor = conf.getint("Version", "VerMinor")
            ver_release = conf.getint("Version", "VerRelease")
        except configparser.NoOptionError as e:
            self.logger.exception(
                "Could not read version information from %s, option info will not be read",
                data_conf_file,
                exc_info=e,
            )
            return None

        opt_name = os.path.basename(os.path.normpath(opt_dir))
        opt_row = await self.data.static.get_opt_by_version_folder(
            self.version, opt_name
        )

        if opt_row is None:
            opt_id = await self.data.static.put_opt(self.version, opt_name, ver_release)

            if opt_id is None:
                return None
        else:
            opt_id = cast(int, opt_row.id)

        self.logger.info(
            "option folder %s (database ID %s) contains v%s.%s.%s",
            opt_name,
            opt_id,
            ver_major,
            ver_minor,
            ver_release,
        )

        return opt_id
