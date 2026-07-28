"""Pop'n Music route registration for Artemis."""

from __future__ import annotations

from core.config import CoreConfig
from core.data import Data
from core.konami.protocol import EamuseInfo, EamuseResponse
from core.konami.router import EamuseRouter, KonamiPlugin

from .repository import PopnRepository
from .versions import SPECS, PopnVersionHandler


class PopnPlugin(KonamiPlugin):
    """Pop'n Music 19 through Unilab route set.

    The old games use ``K39/L39/M39`` with the playerdata module.  Later games
    expose their version in the module name (player22/player23/player24), as
    in the reference Asphyxia plugin.
    """

    game_codes = ("K39", "L39", "M39")

    def __init__(self, cfg: CoreConfig) -> None:
        self.cfg = cfg
        self.data = Data(cfg)
        self._handlers = {
            "v19": PopnVersionHandler(PopnRepository(self.data, "K39"), SPECS["v19"], cfg.konami.popn_force_unlock),
            "v20": PopnVersionHandler(PopnRepository(self.data, "L39"), SPECS["v20"], cfg.konami.popn_force_unlock),
            "v21": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v21"], cfg.konami.popn_force_unlock),
            "v22": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v22"], cfg.konami.popn_force_unlock),
            "v23": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v23"], cfg.konami.popn_force_unlock),
            "v24": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v24"], cfg.konami.popn_force_unlock),
            "v25": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v25"], cfg.konami.popn_force_unlock),
            "v26": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v26"], cfg.konami.popn_force_unlock),
            "v27": PopnVersionHandler(PopnRepository(self.data, "M39"), SPECS["v27"], cfg.konami.popn_force_unlock),
        }

    def register(self, router: EamuseRouter) -> None:
        for code in self.game_codes:
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
                for method, handler_name in (
                    ("common", "info"), ("new", "new"), ("read", "read"),
                    ("start", "start"), ("buy", "buy"), ("read_score", "read_score"),
                    ("write_music", "write_music"), ("write", "write"),
                    ("friend", "friend"),
                ):
                    router.add(code, f"info{prefix}" if method == "common" else f"player{prefix}", method, self._modern(version, handler_name))
            router.fallback(code, self.unhandled)

    def _classic(self, name: str):
        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            version = {"K39": "v19", "L39": "v20", "M39": "v21"}[info.game_code]
            if name == "town":
                response.content = {"result": {"@attr": {"status": "0"}}}
                return
            await getattr(self._handlers[version], name)(info, data, response)
        return handler

    def _modern(self, version: str, name: str):
        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            selected = self._usaneko_version(info.model) if version == "v24" else version
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
