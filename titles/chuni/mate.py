from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
)

from .xversex import ChuniXVerseX


class ChuniMate(ChuniXVerseX):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
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
        return await super().handle_get_user_mate_api_request(data)