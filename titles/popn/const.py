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
