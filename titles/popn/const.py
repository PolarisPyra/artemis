class PopnConstants:
    GAME_CODE = "M39"
    GAME_ABVR = "popn"

    CONFIG_NAME = "popn.yaml"

    VER_BASE = 0
    VER_2 = 1
    VER_3 = 2
    VER_4 = 3
    VER_5 = 4
    VER_6 = 5
    VER_7 = 6
    VER_8 = 7
    VER_9 = 8
    VER_10 = 9
    VER_11 = 10
    VER_IROHA = 11
    VER_CARNIVAL = 12
    VER_FEVER = 13
    VER_ADVENTURE = 14
    VER_PARTY = 15
    VER_MOVIE = 16
    VER_SENGOKU = 17
    VER_TUNE_STREET = 18
    VER_HELLO_POPN = 19
    VER_FANTASIA = 20
    VER_PARK = 21
    VER_LAPISTORIA = 22
    VER_ECLALE = 23
    VER_USANEKO = 24
    VER_PEACE = 25
    VER_KAIMEI = 26
    VER_UNILAB = 27
    VER_JAM_FIZZ = 28
    VER_HI_CHEERS = 29

    VERSION_NAMES = [
        "Pop'n Music",
        "Pop'n Music 2",
        "Pop'n Music 3",
        "Pop'n Music 4",
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
