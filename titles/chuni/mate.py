from typing import Dict

from artemis.config import ArtemisConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
)

from .xversex import ChuniXVerseX


class ChuniMate(ChuniXVerseX):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_MATE

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # CardMaker Should work at this version... right?
        user_data["lastDataVersion"] = "2.50.00"
        return user_data
    
    async def handle_get_user_preview_api_request(self, data):
        return await super().handle_get_user_preview_api_request(data)
    
    async def handle_get_user_favorite_collection_api_request(self, data):
        return await super().handle_get_user_favorite_collection_api_request(data)
    
    async def handle_get_user_mate_api_request(self, data):
        user_id = int(data["userId"])

        rows = await self.data.item.get_all_mates(user_id)
        mate_list = []
        if rows is not None:
            for row in rows:
                mate_list.append(row._asdict())

        return {
            "userId": user_id,
            "length": len(mate_list),
            "userMateList": mate_list,
        }
