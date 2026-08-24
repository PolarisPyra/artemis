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
    VER_STREET = 18
    VER_FANTASIA = 19
    VER_PARK = 20
    VER_LAPISTORIA = 21
    VER_ECLALE = 22
    VER_USANEKO = 23
    VER_PEACE = 24
    VER_KAIMEI = 25
    VER_UNILAB = 26
    VER_JAM_FIZZ = 27
    VER_HI_CHEERS = 29

    VERSION_NAMES = [
        "pop'n music",
        "pop'n music 2",
        "pop'n music 3",
        "pop'n music 4",
        "pop'n music 5",
        "pop'n music 6",
        "pop'n music 7",
        "pop'n music 8",
        "pop'n music 9",
        "pop'n music 10",
        "pop'n music 11",
        "pop'n music 12 いろは",
        "pop'n music 13 カーニバル",
        "pop'n music 14 FEVER!",
        "pop'n music 15 ADVENTURE",
        "pop'n music 16 PARTY♪",
        "pop'n music 17 THE MOVIE",
        "pop'n music 18 せんごく列伝",
        "pop'n music 19 TUNE STREET",
        "pop'n music 20 fantasia",
        "pop'n music Sunny Park",
        "pop'n music ラピストリア",
        "pop'n music éclale",
        "pop'n music うさぎと猫と少年の夢",
        "pop'n music peace",
        "pop'n music 解明リドルズ",
        "pop'n music UniLab",
        "pop'n music Jam&Fizz",
        "pop'n music (reserved)",
        "pop'n music High☆Cheers!!",
    ]

    @classmethod
    def game_ver_to_string(cls, ver: int):
        return cls.VERSION_NAMES[ver]
