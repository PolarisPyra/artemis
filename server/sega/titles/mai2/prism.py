import base64
import os
from typing import Dict

from server.sega.config import ArtemisConfig
from server.sega.titles.mai2.buddiesplus import Mai2BuddiesPlus
from server.sega.titles.mai2.const import Mai2Constants
from server.sega.titles.mai2.config import Mai2Config


class Mai2Prism(Mai2BuddiesPlus):
    def __init__(self, cfg: ArtemisConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_PRISM

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.50.00"
        return user_data

    async def handle_get_user_new_item_list_api_request(self, data: Dict) -> Dict:
        return {"user_id": data["userId"], "userItemList": []}

    # used for downloading music scores online
    async def handle_get_game_music_score_api_request(self, data: Dict) -> Dict:
        if (
            not self.game_config.charts.enable
            or not self.game_config.charts.chart_folder
        ):
            return {
                "gameMusicScore": {
                    "musicId": data["musicId"],
                    "level": data["level"],
                    "type": data["type"],
                    "scoreData": "",
                }
            }

        padded_music_id = str(data["musicId"]).zfill(6)
        padded_level_id = str(data["level"]).zfill(2)
        music_folder = f"music{padded_music_id}"

        if data["type"] == 0:
            target_filename = f"{padded_music_id}_{padded_level_id}.ma2"
        elif data["type"] == 1:
            target_filename = f"{padded_music_id}_{padded_level_id}_L.ma2"
        elif data["type"] == 2:
            target_filename = f"{padded_music_id}_{padded_level_id}_R.ma2"
        else:
            self.logger.error("Invalid MusicScore type!")
            return {
                "gameMusicScore": {
                    "musicId": data["musicId"],
                    "level": data["level"],
                    "type": data["type"],
                    "scoreData": "",
                }
            }

        chart_path = os.path.join(
            self.game_config.charts.chart_folder,
            str(self.version),
            music_folder,
            target_filename,
        )
        if os.path.isfile(chart_path):
            with open(chart_path, "rb") as file:
                file_content = file.read()
                base64_content = base64.b64encode(file_content).decode("ascii")
                return {
                    "gameMusicScore": {
                        "musicId": data["musicId"],
                        "level": data["level"],
                        "type": data["type"],
                        "scoreData": base64_content,
                    }
                }
        else:
            self.logger.warning(
                f"Version {self.version} Chart {target_filename} not found!"
            )
            return {
                "gameMusicScore": {
                    "musicId": data["musicId"],
                    "level": data["level"],
                    "type": data["type"],
                    "scoreData": "",
                }
            }

    async def handle_get_game_kaleidx_scope_api_request(self, data: Dict) -> Dict:
        return {
            "gameKaleidxScopeList": [
                {"gateId": 1, "phaseId": 6},
                {"gateId": 2, "phaseId": 6},
                {"gateId": 3, "phaseId": 6},
                {"gateId": 4, "phaseId": 6},
            ]
        }

    async def handle_get_user_kaleidx_scope_api_request(self, data: Dict) -> Dict:
        # kaleidxscope keyget condition judgement
        # player may get key before GateFound
        for gate in range(1, 5):
            if gate == 1 or gate == 4:
                condition_satisfy = 0
                for condition in Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[gate]:
                    score_list = await self.data.score.get_best_scores(
                        user_id=data["userId"], song_id=condition
                    )
                    if score_list:
                        condition_satisfy = condition_satisfy + 1
                if (
                    len(Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[gate])
                    == condition_satisfy
                ):
                    new_kaleidxscope = {"gateId": gate, "isKeyFound": True}
                    await self.data.score.put_user_kaleidxscope(
                        data["userId"], new_kaleidxscope
                    )

            elif gate == 2:
                user_profile = await self.data.profile.get_profile_detail(
                    user_id=data["userId"], version=self.version
                )
                user_frame = user_profile["frameId"]
                if user_frame == 459504:
                    playlogs = await self.data.score.get_playlogs(
                        user_id=data["userId"], idx=0, limit=0
                    )

                    playlog_dict = {}
                    for playlog in playlogs:
                        playlog_id = playlog["playlogId"]
                        if playlog_id not in playlog_dict:
                            playlog_dict[playlog_id] = []
                        playlog_dict[playlog_id].append(playlog["musicId"])
                    valid_playlogs = []
                    allowed_music = set(Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[2])
                    for playlog_id, music_ids in playlog_dict.items():
                        if len(music_ids) != len(set(music_ids)):
                            continue
                        all_valid = True
                        for mid in music_ids:
                            if mid not in allowed_music:
                                all_valid = False
                                break
                        if all_valid:
                            valid_playlogs.append(playlog_id)

                    if valid_playlogs:
                        new_kaleidxscope = {"gateId": 2, "isKeyFound": True}
                        await self.data.score.put_user_kaleidxscope(
                            data["userId"], new_kaleidxscope
                        )

        kaleidxscope = await self.data.score.get_user_kaleidxscope_list(data["userId"])

        if kaleidxscope is None:
            return {"userId": data["userId"], "userKaleidxScopeList": []}

        kaleidxscope_list = []
        for kaleidxscope_data in kaleidxscope:
            tmp = kaleidxscope_data._asdict()
            tmp.pop("user")
            tmp.pop("id")
            kaleidxscope_list.append(tmp)
        return {"userId": data["userId"], "userKaleidxScopeList": kaleidxscope_list}

    async def handle_upload_user_playlog_list_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        playlog_list = data["userPlaylogList"]

        for playlog in playlog_list:
            await self.data.score.put_playlog(user_id, playlog)

        return {"returnCode": 1, "apiName": "UploadUserPlaylogListApi"}
