from typing import Dict, Optional, Tuple


class PopnConstants:
    GAME_CODE = "M39"
    GAME_ABVR = "popn"

    CONFIG_NAME = "popn.yaml"

    VER_BASE = 0
    VER_2 = 1
    VER_3 = 2
    VER_ANIMELO = 3
    VER_4 = 4
    VER_MICKEY_TUNES = 5
    VER_ANIMELO_2 = 6
    VER_5 = 7
    VER_6 = 8
    VER_7 = 9
    VER_8 = 10
    VER_9 = 11
    VER_10 = 12
    VER_11 = 13
    VER_IROHA = 14
    VER_CARNIVAL = 15
    VER_FEVER = 16
    VER_ADVENTURE = 17
    VER_PARTY = 18
    VER_MOVIE = 19
    VER_SENGOKU = 20
    VER_TUNE_STREET = 21
    VER_HELLO_POPN = 22
    VER_FANTASIA = 23
    VER_PARK = 24
    VER_LAPISTORIA = 25
    VER_ECLALE = 26
    VER_USANEKO = 27
    VER_PEACE = 28
    VER_KAIMEI = 29
    VER_UNILAB = 30
    VER_JAM_FIZZ = 31
    VER_HI_CHEERS = 32

    VERSION_DATECODES: Dict[int, Tuple[int, Optional[int]]] = {
        VER_USANEKO: (2016121400, 2018082100),
        VER_PEACE: (2018082101, 2020092800),
        VER_KAIMEI: (2020092801, 2022090500),
        VER_UNILAB: (2022090501, 2023123123),
        VER_JAM_FIZZ: (2024010100, 2024123123),
        VER_HI_CHEERS: (2025010100, None),
    }

    VERSION_NAMES = [
        "Pop'n Music",
        "Pop'n Music 2",
        "Pop'n Music 3",
        "Pop'n Music アニメロ",
        "Pop'n Music 4",
        "Pop'n Music MICKEY TUNES",
        "Pop'n Music アニメロ2号",
        "Pop'n Music 5",
        "Pop'n Music 6",
        "Pop'n Music 7",
        "Pop'n Music 8",
        "Pop'n Music 9",
        "Pop'n Music 10",
        "Pop'n Music 11",
        "Pop'n Music 12 いろは",
        "Pop'n Music 13 CARNIVAL",
        "Pop'n Music 14 FEVER",
        "Pop'n Music 15 ADVENTURE",
        "Pop'n Music 16 PARTY",
        "Pop'n Music 17 THE MOVIE",
        "Pop'n Music 18 せんごく列伝",
        "Pop'n Music 19 TUNE STREET",
        "HELLO! POP'N MUSIC",
        "Pop'n Music 20 fantasia",
        "Pop'n Music Sunny Park",
        "Pop'n Music ラピストリア",
        "Pop'n Music Éclale",
        "Pop'n Music うさぎと猫と少年の夢",
        "Pop'n Music peace",
        "Pop'n Music 解明リドルズ",
        "Pop'n Music UniLab",
        "Pop'n Music Jam&Fizz",
        "Pop'n Music High☆Cheers!!",
    ]

    @classmethod
    def game_ver_to_string(cls, ver: int):
        return cls.VERSION_NAMES[ver]

    @classmethod
    def datecode_to_version(cls, datecode: int) -> int:
        for version, (start, end) in cls.VERSION_DATECODES.items():
            if datecode >= start and (end is None or datecode <= end):
                return version
        return -1 if datecode < min(start for start, _ in cls.VERSION_DATECODES.values()) else -2
