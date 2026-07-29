from enum import Enum, IntEnum


class ChuniConstants:
    GAME_CODE = "SDBT"
    GAME_CODE_NEW = "SDHD"
    GAME_CODE_INT = "SDGS"
    GAME_CODE_CN = "SDHJ"

    CONFIG_NAME = "chuni.yaml"

    VER_CHUNITHM = 0
    VER_CHUNITHM_PLUS = 1
    VER_CHUNITHM_AIR = 2
    VER_CHUNITHM_AIR_PLUS = 3
    VER_CHUNITHM_STAR = 4
    VER_CHUNITHM_STAR_PLUS = 5
    VER_CHUNITHM_AMAZON = 6
    VER_CHUNITHM_AMAZON_PLUS = 7
    VER_CHUNITHM_CRYSTAL = 8
    VER_CHUNITHM_CRYSTAL_PLUS = 9
    VER_CHUNITHM_PARADISE = 10

    VER_CHUNITHM_NEW = 11
    VER_CHUNITHM_NEW_PLUS = 12
    VER_CHUNITHM_SUN = 13
    VER_CHUNITHM_SUN_PLUS = 14
    VER_CHUNITHM_LUMINOUS = 15
    VER_CHUNITHM_LUMINOUS_PLUS = 16
    VER_CHUNITHM_VERSE = 17
    VER_CHUNITHM_X_VERSE = 18
    VER_CHUNITHM_X_VERSE_X = 19
    VER_CHUNITHM_MATE = 20

    VERSION_NAMES = [
        "CHUNITHM",
        "CHUNITHM PLUS",
        "CHUNITHM AIR",
        "CHUNITHM AIR PLUS",
        "CHUNITHM STAR",
        "CHUNITHM STAR  PLUS",
        "CHUNITHM AMAZON",
        "CHUNITHM AMAZON PLUS",
        "CHUNITHM CRYSTAL",
        "CHUNITHM CRYSTAL PLUS",
        "CHUNITHM PARADISE",
        "CHUNITHM NEW!!",
        "CHUNITHM NEW PLUS!!",
        "CHUNITHM SUN",
        "CHUNITHM SUN PLUS",
        "CHUNITHM LUMINOUS",
        "CHUNITHM LUMINOUS PLUS",
        "CHUNITHM VERSE",
        "CHUNITHM X-VERSE",
        "CHUNITHM X-VERSE-X",
        "CHUNITHM MATE",
    ]

    SCORE_RANK_INTERVALS_OLD = [
        (1007500, "SSS"),
        (1000000, "SS"),
        (975000, "S"),
        (950000, "AAA"),
        (925000, "AA"),
        (900000, "A"),
        (800000, "BBB"),
        (700000, "BB"),
        (600000, "B"),
        (500000, "C"),
        (0, "D"),
    ]

    SCORE_RANK_INTERVALS_NEW = [
        (1009000, "SSS+"),  # New only
        (1007500, "SSS"),
        (1005000, "SS+"),  # New only
        (1000000, "SS"),
        (990000, "S+"),  # New only
        (975000, "S"),
        (950000, "AAA"),
        (925000, "AA"),
        (900000, "A"),
        (800000, "BBB"),
        (700000, "BB"),
        (600000, "B"),
        (500000, "C"),
        (0, "D"),
    ]

    @classmethod
    def game_ver_to_string(cls, ver: int):
        return cls.VERSION_NAMES[ver]


class MapAreaConditionType(IntEnum):
    """
    Condition IDs for the `GetGameMapAreaConditionApi`, `GetGameUCConditionApi`
    and `GetGameLVConditionOpenApi` requests.
    - "Item" or "locked item" refers to the map area, unlock challenge or
    Linked VERSE locked using this system.
    - "Chart ID" refers to musicID \\* 100 + difficulty, where difficulty is 0 for BASIC
    up to 6 for WORLD'S END. For example, Halcyon ULTIMA is 17305.

    The complete list can be obtained by searching for the string `"RankSSS+"` and following
    its only reference in a reverse-engineering suite e.g. Ghidra.
    """

    INVALID = 0
    """
    Invalid condition type. Should cause the hidden item to be automatically unlocked,
    but seemingly only works with map areas.
    """

    MAP_CLEARED = 1
    """Finish the map with ID `conditionId`."""

    MAP_AREA_CLEARED = 2
    """Finish the map area with ID `conditionId`."""

    TROPHY_OBTAINED = 3
    """Unlock the trophy with ID `conditionId`."""

    TROPHY_EQUIPPED = 4
    """
    Equip the trophy with ID `conditionId`. The item is locked again when the trophy is
    unequipped.
    """

    NAMEPLATE_OBTAINED = 5
    """Unlock the nameplate with ID `conditionId`."""

    NAMEPLATE_EQUIPPED = 6
    """
    Equip the nameplate with ID `conditionId`. The item is locked again when the nameplate
    is unequipped.
    """

    CHARACTER_OBTAINED = 7
    """Unlock the character with ID `conditionId`."""

    CHARACTER_EQUIPPED = 8
    """
    Equip the character with ID `conditionId`. The item is locked again when the character
    is unequipped.
    """

    CHARACTER_TRANSFORM_EQUIPPED = 9
    """
    Equip the character, with the character transform ID `conditionId`. The item is locked again
    if the incorrect character is equipped, or the correct character is equipped with the wrong
    transform.
    """

    MUSIC_OBTAINED = 10
    """Unlock the music with ID `conditionId`."""

    AVATAR_ACCESSORY_OBTAINED = 11
    """Unlock the avatar accessory with ID `conditionId`."""

    AVATAR_ACCESSORY_EQUIPPED = 12
    """
    Equip the avatar accessory with ID `conditionId`. The item is locked again when the avatar
    accessory is unequipped.
    """

    MAP_ICON_OBTAINED = 13
    """Unlock the map icon with ID `conditionId`."""

    MAP_ICON_EQUIPPED = 14
    """
    Equip the map icon with ID `conditionId`. The item is locked again when the map icon is
    unequipped.
    """

    SYSTEM_VOICE_OBTAINED = 15
    """Unlock the system voice with ID `conditionId`."""

    SYSTEM_VOICE_EQUIPPED = 16
    """
    Equip the system voice with ID `conditionId`. The item is locked again when the system voice
    is unequipped.
    """

    ALL_JUSTICE_CRITICAL = 17
    """Obtain ALL JUSTICE CRITICAL on the chart given by `conditionId`."""

    RANK_SSSP = 18
    """Obtain rank SSS+ on the chart given by `conditionId`."""

    RANK_SSS = 19
    """Obtain rank SSS on the chart given by `conditionId`."""

    RANK_SSP = 20
    """Obtain rank SS+ on the chart given by `conditionId`."""

    RANK_SS = 21
    """Obtain rank SS on the chart given by `conditionId`."""

    RANK_SP = 22
    """Obtain rank S+ on the chart given by `conditionId`."""

    RANK_S = 23
    """Obtain rank S on the chart given by `conditionId`."""

    RANK_AAA = 24
    """Obtain rank AAA on the chart given by `conditionId`."""

    RANK_AA = 25
    """Obtain rank AA on the chart given by `conditionId`."""

    RANK_A = 26
    """Obtain rank A on the chart given by `conditionId`."""

    MINIMUM_BEST_30_AVERAGE = 27
    """Obtain a best 30 average of at least `conditionId / 100`."""

    ALL_JUSTICE = 28
    """Obtain ALL JUSTICE on the chart given by `conditionId`."""

    FULL_COMBO = 29
    """Obtain FULL COMBO on the chart given by `conditionId`."""

    UNLOCK_CHALLENGE_DISCOVERED = 30
    """Discover/unlock the unlock challenge with ID `conditionId`."""

    UNLOCK_CHALLENGE_CLEARED = 31
    """Clear the unlock challenge with ID `conditionId`."""

    MINIMUM_RATING = 32
    """Obtain a rating of at least `conditionId / 100`."""


class LinkedVerseUnlockConditionType(IntEnum):
    """
    For conditions where it's sensible to have a list of items (basically everything
    except team course+minimum character rank), a list can be separated using either:
        - Semicolon (`;`), which indicates that *all* items in this list must meet
        the condition.
        - Underscore (`_`), which indicates that *at least one* item in this list
        must meet the condition.
    """

    PLAY_SONGS = 33
    """
    Play songs given by `conditionList`, where `conditionList` is a
    list of song IDs.
    """

    COURSE_CLEAR_AND_CLASS_EMBLEM = 34
    """
    Obtain a class emblem (by clearing all courses of a given class) on **any**
    of the classes given by `conditionList`, where `conditionList` is an
    underscore-separated list of class IDs (1 for CLASS I to 6 for CLASS ∞).
    """

    TROPHY_OBTAINED = 35
    """
    Obtain trophies given by `conditionList`, where `conditionList` is a
    list of trophy IDs.
    """

    PLAY_SONGS_IN_FAVORITE = 36
    """
    Play songs given by `conditionList` **from the favorites folder**, where
    `conditionList` is a list of song IDs.
    """

    CLEAR_TEAM_COURSE_WITH_CHARACTER_OF_MINIMUM_RANK = 37
    """
    Clear a team course while equipping a character of minimum rank.
    """

    AVATAR_ACCESSORY_EQUIPPED = 40
    """
    Equip avatar accessories whose IDs are specified by `conditionList`.
    """

    PLAY_SONGS_IN_ONLINE_BATTLE = 41
    """
    Play songs given by `conditionList` **in online battle**, where `conditionList`
    is a list of song IDs.
    """

    MAP_CLEARED = 42
    """
    Finish maps whose IDs are specified by `conditionList`.
    """

    PLAY_SONGS_IN_RECOMMENDED_FOLDER = 43
    """
    Play songs given by `conditionList` **from the recommended music folder**, where
    `conditionList` is a list of song IDs.
    """

    UNLOCKED_SONGS = 44
    """
    Unlock songs given by `conditionList`, where `conditionList` is a list of song IDs.
    """

    LINKED_GATE_CLEARED_SPECIAL = 45
    """
    Clear Linked GATEs given by `conditionList`, where `conditionList` is a list of
    Linked GATE IDs.
    """


class MapAreaConditionLogicalOperator(Enum):
    AND = 1
    OR = 2


class AvatarCategory(Enum):
    WEAR = 1
    HEAD = 2
    FACE = 3
    SKIN = 4
    ITEM = 5
    FRONT = 6
    BACK = 7


class ItemKind(IntEnum):
    NAMEPLATE = 1

    FRAME = 2
    """
    "Frame" is the background for the gauge/score/max combo display
    shown during gameplay. This item cannot be equipped (as of LUMINOUS)
    and is hardcoded to the current game's version.
    """

    TROPHY = 3
    SKILL = 4

    TICKET = 5
    """A statue is also a ticket."""

    PRESENT = 6
    MUSIC_UNLOCK = 7
    MAP_ICON = 8
    SYSTEM_VOICE = 9
    SYMBOL_CHAT = 10
    AVATAR_ACCESSORY = 11

    ULTIMA_UNLOCK = 12
    """This only applies to ULTIMA difficulties that are *not* unlocked by
    SS-ing EXPERT+MASTER.
    """


class FavoriteItemKind(IntEnum):
    MUSIC = 1
    RIVAL = 2
    CHARACTER = 3


class IdlistType(IntEnum):
    NGLIST = 1
    """Songs that have been removed from the game and should not appear in song select."""

    SPECIAL_TICKETS = 3
    """Seems to be for tickets (i.e. the special ticket you get after playing maimai for a credit.)"""

    SPECIAL_PRESENTS = 4


class EventType(IntEnum):
    ANNOUNCEMENT = 1
    MAP_FLAG = 2
    SONG_UNLOCK = 3
    ATTRACT_MOVIE = 4
    RECOMMENDED_SONGS = 5
    ONLINE_FLAG = 6
    COURSE_RELEASE = 7
    QUEST_FLAG = 8
    DUEL_FLAG = 9
    AVATAR_ACCESSORY_UPDATE = 10
    COPYRIGHT_DISPLAY = 11
    PLAY_REWARD_FLAG = 12
    DAILY_BONUS = 13
    MISSION_FLAG = 14
    # where's 15?
    UNLOCK_CHALLENGE_FLAG = 16
