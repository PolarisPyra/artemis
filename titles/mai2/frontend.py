from typing import List
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from os import path
import yaml
import jinja2
from datetime import datetime

from core.frontend import FE_Base, UserSession, PermissionOffset
from core.config import CoreConfig
from .database import Mai2Data
from .config import Mai2Config
from .const import Mai2Constants


class Mai2Frontend(FE_Base):
    def __init__(
        self, cfg: CoreConfig, environment: jinja2.Environment, cfg_dir: str
    ) -> None:
        super().__init__(cfg, environment)
        self.data = Mai2Data(cfg)
        self.game_cfg = Mai2Config()
        if path.exists(f"{cfg_dir}/{Mai2Constants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{Mai2Constants.CONFIG_NAME}"))
            )
        self.nav_name = "maimai"

    def get_routes(self) -> List[Route]:
        return [
            Route("/", self.render_GET, methods=["GET"]),
            Mount(
                "/playlog",
                routes=[
                    Route("/", self.render_GET_playlog, methods=["GET"]),
                    Route("/{index}", self.render_GET_playlog, methods=["GET"]),
                ],
            ),
            Mount(
                "/events",
                routes=[
                    Route("/", self.render_events, methods=["GET"]),
                    Route("/{event_id:int}", self.render_event_edit, methods=["GET"]),
                    Route("/update", self.update_event, methods=["POST"]),
                    Route("/version.change", self.version_change, methods=["POST"]),
                ],
            ),
            Route("/update.name", self.update_name, methods=["POST"]),
            Route("/version.change", self.version_change, methods=["POST"]),
        ]

    async def render_GET(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/mai2/templates/mai2_index.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        incoming_ver = usr_sesh.maimai_version

        if usr_sesh.user_id > 0:
            versions = await self.data.profile.get_all_profile_versions(
                usr_sesh.user_id
            )
            profile = []
            if versions:
                # maimai_version is -1 means it is not initialized yet, select a default version from existing.
                if incoming_ver < 0:
                    usr_sesh.maimai_version = versions[0]["version"]
                profile = await self.data.profile.get_profile_detail(
                    usr_sesh.user_id, usr_sesh.maimai_version
                )
                versions = [x["version"] for x in versions]

            resp = Response(
                template.render(
                    title=f"{self.core_config.server.name} | {self.nav_name}",
                    game_list=self.environment.globals["game_list"],
                    sesh=vars(usr_sesh),
                    user_id=usr_sesh.user_id,
                    profile=profile,
                    version_list=Mai2Constants.VERSION_STRING,
                    versions=versions,
                    cur_version=usr_sesh.maimai_version,
                ),
                media_type="text/html; charset=utf-8",
            )

            if incoming_ver < 0:
                encoded_sesh = self.encode_session(usr_sesh)
                resp.delete_cookie("ARTEMIS_SESH")
                resp.set_cookie("ARTEMIS_SESH", encoded_sesh)
            return resp

        else:
            return RedirectResponse("/gate/", 303)

    async def render_GET_playlog(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/mai2/templates/mai2_playlog.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            if usr_sesh.maimai_version < 0:
                return RedirectResponse("/game/mai2/", 303)
            path_index = request.path_params.get("index")
            if not path_index or int(path_index) < 1:
                index = 0
            else:
                index = int(path_index) - 1  # 0 and 1 are 1st page
            user_id = usr_sesh.user_id
            playlog_count = await self.data.score.get_user_playlogs_count(user_id)
            if playlog_count < index * 20:
                return Response(
                    template.render(
                        title=f"{self.core_config.server.name} | {self.nav_name}",
                        game_list=self.environment.globals["game_list"],
                        sesh=vars(usr_sesh),
                        playlog_count=0,
                    ),
                    media_type="text/html; charset=utf-8",
                )
            playlog = await self.data.score.get_playlogs(user_id, index, 20)
            playlog_with_title = []
            for record in playlog:
                music_chart = await self.data.static.get_music_chart(
                    usr_sesh.maimai_version, record.musicId, record.level
                )
                if music_chart:
                    difficultyNum = music_chart.chartId
                    difficulty = music_chart.difficulty
                    artist = music_chart.artist
                    title = music_chart.title
                else:
                    difficultyNum = 0
                    difficulty = 0
                    artist = "unknown"
                    title = "musicid: " + str(record.musicId)
                playlog_with_title.append(
                    {
                        "raw": record,
                        "title": title,
                        "difficultyNum": difficultyNum,
                        "difficulty": difficulty,
                        "artist": artist,
                    }
                )
            return Response(
                template.render(
                    title=f"{self.core_config.server.name} | {self.nav_name}",
                    game_list=self.environment.globals["game_list"],
                    sesh=vars(usr_sesh),
                    user_id=usr_sesh.user_id,
                    playlog=playlog_with_title,
                    playlog_count=playlog_count,
                ),
                media_type="text/html; charset=utf-8",
            )
        else:
            return RedirectResponse("/gate/", 303)

    async def update_name(self, request: Request) -> bytes:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        form_data = await request.form()
        new_name: str = form_data.get("new_name")
        new_name_full = ""

        if not new_name:
            return RedirectResponse("/gate/?e=4", 303)

        if len(new_name) > 8:
            return RedirectResponse("/gate/?e=8", 303)

        for x in new_name:  # FIXME: This will let some invalid characters through atm
            o = ord(x)
            try:
                if o == 0x20:
                    new_name_full += chr(0x3000)
                elif o < 0x7F and o > 0x20:
                    new_name_full += chr(o + 0xFEE0)
                elif o <= 0x7F:
                    self.logger.warn(f"Invalid ascii character {o:02X}")
                    return RedirectResponse("/gate/?e=4", 303)
                else:
                    new_name_full += x

            except Exception as e:
                self.logger.error(
                    f"Something went wrong parsing character {o:04X} - {e}"
                )
                return RedirectResponse("/gate/?e=4", 303)

        if not await self.data.profile.update_name(usr_sesh.user_id, new_name_full):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/mai2/?s=1", 303)

    async def version_change(self, request: Request):
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if "/events/" in request.url.path:
            resp = RedirectResponse("/game/mai2/events/", 303)
        else:
            resp = RedirectResponse("/game/mai2/", 303)

        if usr_sesh.user_id > 0:
            form_data = await request.form()
            maimai_version = form_data.get("version")
            self.logger.info(f"version change to: {maimai_version}")
            if maimai_version.isdigit():
                usr_sesh.maimai_version = int(maimai_version)
                encoded_sesh = self.encode_session(usr_sesh)
                self.logger.debug(f"Created session with JWT {encoded_sesh}")
                resp.set_cookie("ARTEMIS_SESH", encoded_sesh)
            return resp
        else:
            return RedirectResponse("/gate/", 303)

    async def render_events(self, request: Request) -> Response:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        if not self.test_perm(usr_sesh.permissions, PermissionOffset.SYSADMIN):
            return RedirectResponse("/game/mai2/", 303)

        template = self.environment.get_template(
            "titles/mai2/templates/events/mai2_events.jinja"
        )

        incoming_ver = usr_sesh.maimai_version
        evts = []

        if incoming_ver < 0:
            usr_sesh.maimai_version = Mai2Constants.VER_MAIMAI_DX

        event_list = await self.data.static.get_game_events(usr_sesh.maimai_version)
        self.logger.info(f"Get events for v{usr_sesh.maimai_version}")

        for event in event_list:
            evts.append(
                {
                    "id": event["id"],
                    "version": event["version"],
                    "eventId": event["eventId"],
                    "eventType": event["type"],
                    "name": event["name"],
                    "startDate": event["startDate"].strftime("%x %X"),
                    "enabled": "true" if event["enabled"] else "false",
                }
            )

        resp = Response(
            template.render(
                title=f"{self.core_config.server.name} | {self.nav_name} Events",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                version_list=Mai2Constants.VERSION_STRING,
                events=evts,
            ),
            media_type="text/html; charset=utf-8",
        )

        if incoming_ver < 0:
            encoded_sesh = self.encode_session(usr_sesh)
            resp.delete_cookie("ARTEMIS_SESH")
            resp.set_cookie("ARTEMIS_SESH", encoded_sesh)

        return resp

    async def render_event_edit(self, request: Request) -> Response:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        if not self.test_perm(usr_sesh.permissions, PermissionOffset.SYSADMIN):
            return RedirectResponse("/game/mai2/", 303)

        template = self.environment.get_template(
            "titles/mai2/templates/events/mai2_event_edit.jinja"
        )

        evt_id = request.path_params.get("event_id")

        event_id = await self.data.static.get_event_by_id(evt_id)
        if not event_id:
            return RedirectResponse("/game/mai2/events/", 303)

        return Response(
            template.render(
                title=f"{self.core_config.server.name} | {self.nav_name} Edit Event {evt_id}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=usr_sesh.user_id,
                version_list=Mai2Constants.VERSION_STRING,
                cur_version=usr_sesh.maimai_version,
                event=event_id._asdict(),
            ),
            media_type="text/html; charset=utf-8",
        )

    async def update_event(self, request: Request) -> RedirectResponse:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        if not self.test_perm(usr_sesh.permissions, PermissionOffset.SYSADMIN):
            return RedirectResponse("/game/mai2/", 303)

        form_data = await request.form()
        print(form_data)
        event_id: int = form_data.get("evtId", None)
        new_enabled: bool = bool(form_data.get("evtEnabled", False))
        try:
            new_start_date: datetime = datetime.strptime(
                form_data.get("evtStart", None), "%Y-%m-%dT%H:%M:%S"
            )
        except:
            new_start_date = None

        print(f"{event_id} {new_enabled} {new_start_date}")
        if event_id is None or new_start_date is None:
            return RedirectResponse("/game/mai2/events/?e=4", 303)

        await self.data.static.update_event_by_id(
            int(event_id), new_enabled, new_start_date
        )

        return RedirectResponse("/game/mai2/events/?s=1", 303)
