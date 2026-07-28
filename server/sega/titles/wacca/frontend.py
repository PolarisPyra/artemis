from typing import List
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response
from os import path
import yaml
import jinja2

from server.sega.frontend import FE_Base, UserSession
from server.sega.config import ArtemisConfig
from server.sega.titles.wacca.database import WaccaData
from server.sega.titles.wacca.config import WaccaConfig
from server.sega.titles.wacca.const import WaccaConstants


class WaccaFrontend(FE_Base):
    def __init__(
        self, cfg: ArtemisConfig, environment: jinja2.Environment, cfg_dir: str
    ) -> None:
        super().__init__(cfg, environment)
        self.data = WaccaData(cfg)
        self.game_cfg = WaccaConfig()
        if path.exists(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"))
            )
        self.nav_name = "Wacca"

    def get_routes(self) -> List[Route]:
        return [Route("/", self.render_GET, methods=["GET"])]

    async def render_GET(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "server/sega/titles/wacca/templates/wacca_index.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        return Response(
            template.render(
                title=f"{self.artemis_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
            ),
            media_type="text/html; charset=utf-8",
        )
