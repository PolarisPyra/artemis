import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from core.config import CoreConfig
from titles.ongeki.const import OngekiConstants

from .brightmemory import OngekiBrightMemory
from .config import OngekiConfig


class OngekiReFresh(OngekiBrightMemory):
    # Custom consolidated login endpoint (GetLoginBundleApi). It folds the ~40
    # per-call login requests into a single response so a remote client pays one
    # network round-trip instead of ~40. The response is split into a "static"
    # group (generic, identical for every user on this version -> cacheable) and
    # a "user" group (per-user, fetched fresh every time).
    BUNDLE_VERSION = 1
    # How long the assembled generic group is cached in-process. Static game data
    # only changes on an importer run, so a few minutes is plenty; reboot times in
    # gameSetting are computed fresh per request and not part of this cache.
    STATIC_BUNDLE_TTL = 300
    # Page size used when collecting paginated collections in a single internal
    # call. Far larger than any real account; a loop backstops it regardless.
    BUNDLE_PAGE_SIZE = 100000
    # Cap concurrent per-user section queries below the shared DB pool ceiling
    # (default async pool is 5 + 10 overflow = 15) so no section starves waiting
    # for a connection — a starved section would otherwise be silently nulled.
    BUNDLE_MAX_CONCURRENCY = 10
    # internal_ver -> (expires_at monotonic, payload). Class-scoped because the
    # generic group is identical across the (single) servlet instance per version.
    _static_tables_cache: Dict[int, Tuple[float, Dict[str, Any]]] = {}

    def __init__(self, core_cfg: CoreConfig, game_cfg: OngekiConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = OngekiConstants.VER_ONGEKI_REFRESH

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.50.00"
        ret["gameSetting"]["onlineDataVersion"] = "1.50.00"

        return ret
    
    async def handle_get_user_preview_api_request(self, data: Dict) -> Dict:
        profile = await self.data.profile.get_profile_preview(
            data["userId"], self.version
        )

        if profile is None:
            return {
                "userId": data["userId"],
                "isLogin": False,
                "lastLoginDate": "0000-00-00 00:00:00",
                "userName": "",
                "reincarnationNum": 0,
                "level": 0,
                "exp": 0,
                "playerRating": 0,
                "newPlayerRating": 0,
                "lastGameId": "",
                "lastRomVersion": "",
                "lastDataVersion": "",
                "lastPlayDate": "",
                "nameplateId": 0,
                "trophyId": 0,
                "cardId": 0,
                "dispPlayerLv": 0,
                "dispRating": 0,
                "dispBP": 0,
                "headphone": 0,
                "banStatus": 0,
                "isWarningConfirmed": True,
                "lastEmoneyBrand": 0,
                "lastEmoneyCredit": 0,
            }

        return {
            "userId": data["userId"],
            "isLogin": False,
            "lastLoginDate": profile["lastPlayDate"],
            "userName": profile["userName"],
            "reincarnationNum": profile["reincarnationNum"],
            "level": profile["level"],
            "exp": profile["exp"],
            "playerRating": profile["playerRating"],
            "newPlayerRating": profile["newPlayerRating"],
            "lastGameId": profile["lastGameId"],
            "lastRomVersion": profile["lastRomVersion"],
            "lastDataVersion": profile["lastDataVersion"],
            "lastPlayDate": profile["lastPlayDate"],
            "nameplateId": profile["nameplateId"],
            "trophyId": profile["trophyId"],
            "cardId": profile["cardId"],
            "dispPlayerLv": profile["dispPlayerLv"],
            "dispRating": profile["dispRating"],
            "dispBP": profile["dispBP"],
            "headphone": profile["headphone"],
            "banStatus": profile["banStatus"],
            "isWarningConfirmed": True,
            "lastEmoneyBrand": 0,
            "lastEmoneyCredit": 0,
        }

    async def handle_get_user_skin_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        skin_rows = await self.data.item.get_skins(user_id)
        skin_list = []

        for row in (skin_rows or []):
            data = row._asdict()
            data.pop("id")
            data.pop("user")

            skin_list.append(data)

        return {
            "userId": user_id,
            "length": len(skin_list),
            "userSkinList": skin_list,
        }

    async def handle_get_user_event_map_api_request(self, data: Dict[str, int]) -> Dict[str, Any]:
        user_id = data["userId"]
        event_id = data["eventId"]
        map_id = data["mapId"]
        event_map_row = await self.data.item.get_event_map(user_id, event_id, map_id)

        if event_map_row is None:
            return {
                "userId": user_id,
                "userEventMap": {},
            }

        event_map = event_map_row._asdict()
        event_map.pop("id")
        event_map.pop("user")

        return {
            "userId": user_id,
            "userEventMap": event_map,
        }

    # ------------------------------------------------------------------ #
    # Consolidated login bundle
    # ------------------------------------------------------------------ #

    async def handle_get_login_bundle_api_request(self, data: Dict) -> Dict:
        """Return all login data in one response (see class docstring).

        Request: ``{"userId": int, "staticVersion"?: str}``. If ``staticVersion``
        matches the current generic-group ``cacheKey``, the static body is omitted
        so a client that already cached it skips re-downloading it.
        """
        user_id: int = data["userId"]

        # gameSetting is computed fresh (no DB, time-sensitive reboot window); the
        # DB-backed tables come from the in-process TTL cache.
        game_setting = await self.handle_get_game_setting_api_request({})
        cache_key = f"{self.version}:{game_setting['gameSetting']['dataVersion']}"

        if data.get("staticVersion") == cache_key:
            static_group: Dict[str, Any] = {"cacheKey": cache_key}
        else:
            static_group = {
                "cacheKey": cache_key,
                "gameSetting": game_setting,
                **await self._get_static_tables(),
            }

        user_group = await self._get_user_bundle(user_id)

        return {
            "userId": user_id,
            "bundleVersion": self.BUNDLE_VERSION,
            "static": static_group,
            "user": user_group,
        }

    async def _get_static_tables(self) -> Dict[str, Any]:
        """Assemble (and cache) the generic, DB-backed game data group."""
        cached = self._static_tables_cache.get(self.version)
        if cached is not None and cached[0] > time.monotonic():
            return cached[1]

        # GetGameRanking/GetGameEvent echo a "type" field but ignore it for filtering.
        keys = [
            "gameEvent",
            "gameRanking",
            "gamePoint",
            "gameReward",
            "gamePresent",
            "gameTechMusic",
            "gameMusicReleaseState",
        ]
        gathered = await asyncio.gather(
            self.handle_get_game_event_api_request({"type": 1}),
            self.handle_get_game_ranking_api_request({"type": 1}),
            self.handle_get_game_point_api_request({}),
            self.handle_get_game_reward_api_request({}),
            self.handle_get_game_present_api_request({}),
            self.handle_get_game_tech_music_api_request({}),
            self.handle_get_game_music_release_state_api_request({}),
            return_exceptions=True,
        )

        tables = {k: self._unwrap(g, k) for k, g in zip(keys, gathered)}

        # Don't cache a partially-failed assembly; let the next login retry it.
        if not any(isinstance(g, Exception) for g in gathered):
            self._static_tables_cache[self.version] = (
                time.monotonic() + self.STATIC_BUNDLE_TTL,
                tables,
            )
        return tables

    async def _get_user_bundle(self, user_id: int) -> Dict[str, Any]:
        """Assemble the per-user group by reusing the individual Get*Api handlers."""
        req = {"userId": user_id}

        # (output key, handler, key to lift out of the handler's response)
        sections: List[Tuple[str, Callable[[Dict], Awaitable[Dict]], Optional[str]]] = [
            ("preview", self.handle_get_user_preview_api_request, None),
            ("userData", self.handle_get_user_data_api_request, "userData"),
            ("userOption", self.handle_get_user_option_api_request, "userOption"),
            ("userRegionList", self.handle_get_user_region_api_request, "userRegionList"),
            ("userCardList", self.handle_get_user_card_api_request, "userCardList"),
            ("userCharacterList", self.handle_get_user_character_api_request, "userCharacterList"),
            ("userDeckList", self.handle_get_user_deck_by_key_api_request, "userDeckList"),
            ("userSkinList", self.handle_get_user_skin_api_request, "userSkinList"),
            ("userMusicItemList", self.handle_get_user_music_item_api_request, "userMusicItemList"),
            ("userBossList", self.handle_get_user_boss_api_request, "userBossList"),
            ("userStoryList", self.handle_get_user_story_api_request, "userStoryList"),
            ("userChapterList", self.handle_get_user_chapter_api_request, "userChapterList"),
            ("userMemoryChapterList", self.handle_get_user_memory_chapter_api_request, "userMemoryChapterList"),
            ("userTechCountList", self.handle_get_user_tech_count_api_request, "userTechCountList"),
            ("userRecentRatingList", self.handle_get_user_recent_rating_api_request, "userRecentRatingList"),
            ("userRatinglogList", self.handle_get_user_ratinglog_api_request, "userRatinglogList"),
            ("userEventPointList", self.handle_get_user_event_point_api_request, "userEventPointList"),
            ("userEventRankingList", self.handle_get_user_event_ranking_api_request, "userEventRankingList"),
            ("userMissionPointList", self.handle_get_user_mission_point_api_request, "userMissionPointList"),
            ("userLoginBonusList", self.handle_get_user_login_bonus_api_request, "userLoginBonusList"),
            ("userScenarioList", self.handle_get_user_scenario_api_request, "userScenarioList"),
            ("userTradeItemList", self.handle_get_user_trade_item_api_request, "userTradeItemList"),
            ("userEventMusicList", self.handle_get_user_event_music_api_request, "userEventMusicList"),
            ("userTechEventList", self.handle_get_user_tech_event_api_request, "userTechEventList"),
            ("userTechEventRankingList", self.handle_get_user_tech_event_ranking_api_request, "userTechEventRankingList"),
            ("userKopList", self.handle_get_user_kop_api_request, "userKopList"),
        ]

        async def run(handler: Callable[[Dict], Awaitable[Dict]], section_req: Dict, key: Optional[str]) -> Any:
            resp = await handler(section_req)
            if not isinstance(resp, dict):
                return resp
            # key=None means the whole response is the payload (e.g. preview).
            return resp if key is None else resp.get(key)

        coros: List[Awaitable[Any]] = [run(h, req, key) for _, h, key in sections]
        labels: List[str] = [out_key for out_key, _, _ in sections]

        # Activity reads "kind"; kind=None pulls every activity kind at once.
        coros.append(run(self.handle_get_user_activity_api_request, {"userId": user_id, "kind": None}, "userActivityList"))
        labels.append("userActivityList")
        # Paginated / multi-call collections collected in full.
        coros.append(self._collect_paginated(self.handle_get_user_music_api_request, dict(req), "userMusicList"))
        labels.append("userMusicList")
        coros.append(self._collect_user_items(user_id))
        labels.append("userItemList")
        coros.append(self._collect_rivals(user_id))
        labels.append("rivals")

        # A single broken section must not sink the whole bundle, so failures are
        # logged and nulled rather than raised (mirrors the resilience of the
        # individual per-endpoint calls this replaces).
        gathered = await self._bounded_gather(coros)
        return {
            label: self._unwrap(result, label)
            for label, result in zip(labels, gathered)
        }

    async def _bounded_gather(self, coros: List[Awaitable[Any]]) -> List[Any]:
        """gather() capped at BUNDLE_MAX_CONCURRENCY, returning exceptions inline."""
        sem = asyncio.Semaphore(self.BUNDLE_MAX_CONCURRENCY)

        async def _run(coro: Awaitable[Any]) -> Any:
            async with sem:
                return await coro

        return await asyncio.gather(
            *(_run(c) for c in coros), return_exceptions=True
        )

    def _unwrap(self, result: Any, label: str) -> Any:
        """Log-and-null any section that raised, so the bundle degrades gracefully."""
        if isinstance(result, BaseException):
            self.logger.warning(f"login bundle: section '{label}' failed: {result}")
            return None
        return result

    async def _collect_paginated(
        self,
        handler: Callable[[Dict], Awaitable[Dict]],
        base_req: Dict,
        list_key: str,
    ) -> List[Any]:
        """Drive a nextIndex/maxCount handler to completion and return the full list."""
        collected: List[Any] = []
        next_idx = 0
        while True:
            resp = await handler({**base_req, "nextIndex": next_idx, "maxCount": self.BUNDLE_PAGE_SIZE})
            collected.extend(resp.get(list_key, []) or [])
            next_idx = resp.get("nextIndex", 0)
            if not next_idx:
                break
        return collected

    async def _collect_user_items(self, user_id: int) -> List[Dict]:
        """All item kinds at once (GetUserItemApi is kind-paged; the data layer isn't).

        Each row keeps its ``itemKind`` so the client can group as needed.
        """
        rows = await self.data.item.get_items(user_id)
        items: List[Dict] = []
        for row in rows or []:
            tmp = row._asdict()
            tmp.pop("id", None)
            tmp.pop("user", None)
            items.append(tmp)
        return items

    async def _collect_rivals(self, user_id: int) -> Dict[str, Any]:
        rival_resp = await self.handle_get_user_rival_api_request({"userId": user_id})
        rival_list = rival_resp.get("userRivalList", []) or []

        rival_data_resp = await self.handle_get_user_rival_data_api_request(
            {"userId": user_id, "userRivalList": rival_list}
        )

        rival_music: Dict[str, List[Any]] = {}
        for rival in rival_list:
            rival_id = rival["rivalUserId"]
            rival_music[str(rival_id)] = await self._collect_paginated(
                self.handle_get_user_rival_music_api_request,
                {"userId": user_id, "rivalUserId": rival_id},
                "userRivalMusicList",
            )

        return {
            "userRivalList": rival_list,
            "userRivalDataList": rival_data_resp.get("userRivalDataList", []),
            "userRivalMusic": rival_music,
        }

