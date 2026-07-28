"""Pop'n Music route registration for Artemis."""

from __future__ import annotations

from server.sega.config import ArtemisConfig
from server.sega.data import Data
from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter

from .repository import PopnRepository
from .hello import PopnHelloHandler
from .versions import SPECS, PopnVersionHandler


class PopnRoutes:
    """Pop'n Music 19 through Unilab route set.

    The old games use ``K39/L39/M39`` with the playerdata module.  Later games
    expose their version in the module name (player22/player23/player24), as
    in the corresponding Pop'n protocol revisions.
    """

    game_codes = ("K39", "L39", "M39", "JMP")

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.cfg = cfg
        self.data = Data(cfg)
        self.hello = PopnHelloHandler(self.data)
        self._handlers = {
            "v19": PopnVersionHandler(
                PopnRepository(self.data, "K39"),
                SPECS["v19"],
                cfg.konami.popn_force_unlock,
            ),
            "v20": PopnVersionHandler(
                PopnRepository(self.data, "L39"),
                SPECS["v20"],
                cfg.konami.popn_force_unlock,
            ),
            "v21": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v21"],
                cfg.konami.popn_force_unlock,
            ),
            "v22": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v22"],
                cfg.konami.popn_force_unlock,
            ),
            "v23": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v23"],
                cfg.konami.popn_force_unlock,
            ),
            "v24": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v24"],
                cfg.konami.popn_force_unlock,
            ),
            "v25": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v25"],
                cfg.konami.popn_force_unlock,
            ),
            "v26": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v26"],
                cfg.konami.popn_force_unlock,
            ),
            "v27": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v27"],
                cfg.konami.popn_force_unlock,
            ),
        }

    def register(self, router: EamuseRouter) -> None:
        for code in self.game_codes[:3]:
            for module, method, handler_name in (
                ("game", "get", "info"),
                ("playerdata", "new", "new"),
                ("playerdata", "conversion", "new"),
                ("playerdata", "get", "read"),
                ("playerdata", "set", "write"),
                ("playerdata", "friend", "friend"),
                ("playerdata", "town", "town"),
            ):
                router.add(code, module, method, self._classic(handler_name))

            for version_number, version in ((22, "v22"), (23, "v23"), (24, "v24")):
                prefix = f"{version_number}"
                methods = {
                    22: ("new", "read", "write_music", "write", "friend"),
                    23: (
                        "new",
                        "read",
                        "start",
                        "buy",
                        "read_score",
                        "write_music",
                        "write",
                        "friend",
                    ),
                    24: (
                        "new",
                        "read",
                        "start",
                        "buy",
                        "read_score",
                        "write_music",
                        "write",
                        "friend",
                    ),
                }[version_number]
                for method in methods:
                    handler_name = method
                    router.add(
                        code,
                        f"player{prefix}",
                        method,
                        self._modern(version, handler_name),
                    )
                router.add(
                    code, f"info{prefix}", "common", self._modern(version, "info")
                )

            # Hi Cheers labels its common game-data call ``info23.common``
            # even though the cabinet model is M39.
            router.add(code, "info23", "common", self._modern("v21", "info"))

            # M39/Hi Cheers still exposes the original generic XRPC module
            # names in addition to the versioned playerdata modules.  The
            # DLL registers these methods as CXrpcPlayer* classes.  Reuse the
            # established v21 persistence handlers so both naming schemes
            # address the same profile and score documents.
            generic = {
                "new": "new",
                "conversion": "new",
                "read": "read",
                "write": "write",
                "start": "start",
                "delete": "success",
                "end": "success",
                "logout": "success",
                "read_friend": "friend",
                "write_music": "write_music",
                "update_ranking": "success",
                "write_course": "write",
                "read_score": "read_score",
                "shop": "buy",
                "read_option": "read",
                "tsumtsum": "success",
            }
            for method, handler_name in generic.items():
                handler = (
                    self._modern("v21", handler_name)
                    if handler_name != "success"
                    else self.unhandled
                )
                router.add(code, "player", method, handler)
            router.fallback(code, self.unhandled)

        for method in ("common", "shop", "new", "load", "load_m", "save", "save_m"):
            router.add("JMP", "game", method, self._hello(method))
        router.fallback("JMP", self.unhandled)
        for game_code in self.game_codes:
            router.webui(game_code, self.webui_event)

    async def webui_event(self, name: str, data: dict) -> None:
        """Handle Pop'n profile, rival, and unlock WebUI events."""
        repository = self._handlers["v21"].repo
        if name == "updatePnmPlayerInfo":
            await repository.update_profile_name(
                str(data.get("refid", "")), str(data.get("name", ""))
            )
        elif name == "addRival":
            await repository.add_rival(
                str(data.get("refid", "")), str(data.get("rivalid", ""))
            )
        elif name == "deleteRival":
            await repository.delete_rival(
                str(data.get("refid", "")), str(data.get("rivalid", ""))
            )
        elif name == "setUnlockState":
            await self.hello.set_unlock_state(data)

    def _hello(self, name: str):
        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            await getattr(self.hello, name)(info, data, response)

        return handler

    def _classic(self, name: str):
        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            version = {"K39": "v19", "L39": "v20", "M39": "v21"}[info.game_code]
            if name == "town":
                await self._handlers[version].town(info, data, response)
                return
            await getattr(self._handlers[version], name)(info, data, response)

        return handler

    def _modern(self, version: str, name: str):
        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            selected = (
                self._usaneko_version(info.model) if version == "v24" else version
            )
            await getattr(self._handlers[selected], name)(info, data, response)

        return handler

    @staticmethod
    def _usaneko_version(model: str) -> str:
        try:
            timestamp = int(model.rsplit(":", 1)[1])
        except (IndexError, ValueError):
            return "v24"
        if timestamp >= 2022091300:
            return "v27"
        if timestamp >= 2021042600:
            return "v26"
        if timestamp >= 2018101700:
            return "v25"
        return "v24"

    async def unhandled(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.status = 0
