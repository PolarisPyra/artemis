from typing import Dict

from core.config import CoreConfig
from titles.mai2.prism import Mai2Prism
from titles.mai2.const import Mai2Constants
from titles.mai2.config import Mai2Config


class Mai2PrismPlus(Mai2Prism):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_PRISM_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.55.00"
        return user_data

    async def handle_upsert_client_play_time_api_request(self, data: Dict) -> Dict:
        return {"returnCode": 1, "apiName": "UpsertClientPlayTimeApi"}

    async def handle_get_game_kaleidx_scope_api_request(self, data: Dict) -> Dict:
        return {
            "gameKaleidxScopeList": [
                {"gateId": 1, "phaseId": 6},
                {"gateId": 2, "phaseId": 6},
                {"gateId": 3, "phaseId": 6},
                {"gateId": 4, "phaseId": 6},
                {"gateId": 5, "phaseId": 6},
                {"gateId": 6, "phaseId": 6},
                {"gateId": 7, "phaseId": 6},
                {"gateId": 8, "phaseId": 6},
                {"gateId": 9, "phaseId": 6},
                {"gateId": 10, "phaseId": 13},
            ]
        }

    async def handle_get_user_kaleidx_scope_api_request(self, data: Dict) -> Dict:
        # kaleidxscope keyget condition judgement
        # player may get key before GateFound
        for gate in range(1, 11):
            if gate == 1 or gate == 4 or gate == 6:
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

            elif gate == 5:
                playlogs = await self.data.score.get_playlogs(
                    user_id=data["userId"], idx=0, limit=0
                )
                allowed_music = set(Mai2Constants.KALEIDXSCOPE_KEY_CONDITION[5])
                valid_playlogs = []

                for playlog in playlogs:
                    if playlog["extBool2"] == 1 and playlog["musicId"] in allowed_music:
                        valid_playlogs.append(
                            playlog["playlogId"]
                        )  # 直接记录 playlogId
                if valid_playlogs:
                    new_kaleidxscope = {"gateId": 5, "isKeyFound": True}
                    await self.data.score.put_user_kaleidxscope(
                        data["userId"], new_kaleidxscope
                    )

            elif gate == 7:
                played_kaleidxscope_list = (
                    await self.data.score.get_user_kaleidxscope_list(data["userId"])
                )
                check_results = {}
                for i in range(1, 7):
                    check_results[i] = False
                    for played_kaleidxscope in played_kaleidxscope_list:
                        if played_kaleidxscope[2] == i and played_kaleidxscope[5]:
                            check_results[i] = True
                            break
                all_true = all(check_results.values())

                if all_true:
                    new_kaleidxscope = {"gateId": 7, "isKeyFound": True}
                    await self.data.score.put_user_kaleidxscope(
                        data["userId"], new_kaleidxscope
                    )

            elif gate == 10:
                played_kaleidxscope_list = (
                    await self.data.score.get_user_kaleidxscope_list(data["userId"])
                )
                for played_kaleidxscope in played_kaleidxscope_list:
                    if played_kaleidxscope[2] == 9 and played_kaleidxscope[5]:
                        new_kaleidxscope = {
                            "gateId": 10,
                            "isGateFound": True,
                            "isKeyFound": True,
                        }
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
