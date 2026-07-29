"""Pop'n Music Hi Cheers! protocol compatibility.

Hi Cheers keeps the M39 game code and the UniLab profile layout, but its
current cabinet advertises a few legacy module names.  The cabinet uses those
names during login, so they must be handled by the same inherited profile
implementation rather than falling through to an empty e-amusement response.
"""

from core.eamuse import EAProtocol
from core.config import CoreConfig
from core.eaapi import XMLNode, Type

from .config import PopnConfig
from .const import PopnConstants
from .jamfizz import PopnJamFizz


class PopnHiCheers(PopnJamFizz):
    """Hi Cheers title handler, extending the UniLab protocol implementation."""

    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, game_config, protocol)
        self.version = PopnConstants.VER_HI_CHEERS
        # These are the services advertised by the captured M39 Hi Cheers PCB.
        self.extra_services.update({"local3": ""})

    async def handle_pcb_boot(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_pcb_error(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_pcb_write(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_info_common(self, request: XMLNode) -> XMLNode:
        """Serve Hi Cheers' legacy ``info.common`` alias.

        The response fields are shared with the inherited info24 response;
        only the root module name differs in the captured protocol.
        """
        root = await self.handle_info24_common(request)
        root.name = "info"
        return root

    async def handle_player_read(self, request: XMLNode) -> XMLNode:
        """Serve the M39 ``player.read`` login request.

        Hi Cheers sends the legacy module name but expects the modern profile
        payload.  Reuse the inherited profile response and add the legacy
        ``base`` block used by the captured cabinet.
        """
        root = await self.handle_player24_read(request)
        root.name = "player"

        config = next((child for child in root.children if child.name == "config"), None)
        if config is not None and not any(child.name == "disp_setting" for child in config.children):
            category = next(
                (index for index, child in enumerate(config.children) if child.name == "chara_category"),
                len(config.children),
            )
            config.children.insert(category + 1, XMLNode("disp_setting", Type.S8, 0))

        if config is not None:
            disp_setting = next(
                (index for index, child in enumerate(config.children) if child.name == "disp_setting"),
                len(config.children) - 1,
            )
            legacy_config_fields = (
                ("h_vol", Type.S8),
                ("hiscore_disp", Type.S8),
                ("lane_type", Type.S8),
                ("brightness", Type.S8),
                ("key_beam", Type.S8),
                ("lane_line", Type.S8),
            )
            for offset, (name, field_type) in enumerate(legacy_config_fields, start=1):
                if not any(child.name == name for child in config.children):
                    config.children.insert(disp_setting + offset, XMLNode(name, field_type, 0))

        option = next((child for child in root.children if child.name == "option"), None)
        if option is not None:
            guide_se = next(
                (index for index, child in enumerate(option.children) if child.name == "guide_se"),
                len(option.children),
            )
            if not any(child.name == "guide_se_vol" for child in option.children):
                option.children.insert(guide_se + 1, XMLNode("guide_se_vol", Type.U8, 0))

            lift_rate = next(
                (index for index, child in enumerate(option.children) if child.name == "lift_rate"),
                len(option.children),
            )
            if not any(child.name == "judge_ad" for child in option.children):
                option.children.insert(lift_rate + 1, XMLNode("judge_ad", Type.S8, 0))

            judge_ad = next(
                (index for index, child in enumerate(option.children) if child.name == "judge_ad"),
                len(option.children),
            )
            if not any(child.name == "roof" for child in option.children):
                option.children.insert(judge_ad + 1, XMLNode("roof", Type.S16, 0))
            roof = next(
                (index for index, child in enumerate(option.children) if child.name == "roof"),
                len(option.children),
            )
            if not any(child.name == "long_pop" for child in option.children):
                option.children.insert(roof + 1, XMLNode("long_pop", Type.Bool, False))

        account = next((child for child in root.children if child.name == "account"), None)
        if account is not None:
            base = XMLNode.void("base")
            for field in (
                "name", "g_pm_id", "staff", "is_conv", "item_type", "item_id",
                "license_data", "active_fr_num", "total_play_cnt", "today_play_cnt",
                "consecutive_days", "total_days", "interval_day", "latest_music",
                "my_best", "play_id", "start_type", "tutorial", "area_id",
                "read_news", "nice", "favorite_chara", "special_area",
                "chocolate_charalist", "chocolate_sp_chara", "chocolate_pass_cnt",
                "chocolate_hon_cnt", "teacher_setting", "welcom_pack", "use_navi",
                "ranking_node", "chara_ranking_kind_id", "navi_evolution_flg",
                "ranking_news_last_no", "power_point", "player_point",
                "power_point_list", "card_again_count", "sp_riddles_id",
            ):
                source = next((child for child in account.children if child.name == field), None)
                if source is not None:
                    base.children.append(source)
            root.children.append(base)

        try:
            submitted_name = request.xpath("player/name").value
        except Exception:
            submitted_name = None
        if submitted_name and account is not None:
            name = next((child for child in account.children if child.name == "name"), None)
            if name is not None:
                name.value = submitted_name

        root.attributes["status"] = "0"
        return root

    async def handle_player_write(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_start(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_end(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_new(self, request: XMLNode) -> XMLNode:
        # Hi Cheers expects the newly-created profile payload immediately
        # after name selection.  An empty status-only response is treated as
        # a failed receiver operation and returns the cabinet to the title
        # screen.
        return await self.handle_player_read(request)

    async def handle_player_logout(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_conversion(self, request: XMLNode) -> XMLNode:
        return await self.handle_player_read(request)

    async def handle_player_write_music(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_friend(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_write_course(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_update_ranking(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_buy(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_read_score(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_tsumtsum(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_read_option(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_loctest24_log(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("loctest24")

    async def handle_lobby24_update(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("lobby24")

    async def handle_lobby24_delete(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("lobby24")

    async def handle_sppass_open(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("sppass")

    async def handle_sppass_lookup(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("sppass")

    async def handle_sppass_close(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("sppass")
