class Mai2Constants:
    GRADE = {
        "D": 0,
        "C": 1,
        "B": 2,
        "BB": 3,
        "BBB": 4,
        "A": 5,
        "AA": 6,
        "AAA": 7,
        "S": 8,
        "S+": 9,
        "SS": 10,
        "SS+": 11,
        "SSS": 12,
        "SSS+": 13,
    }
    FC = {"None": 0, "FC": 1, "FC+": 2, "AP": 3, "AP+": 4}
    SYNC = {"None": 0, "FS": 1, "FS+": 2, "FDX": 3, "FDX+": 4}

    DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    GAME_CODE = "SBXL"
    GAME_CODE_GREEN = "SBZF"
    GAME_CODE_ORANGE = "SDBM"
    GAME_CODE_PINK = "SDCQ"
    GAME_CODE_MURASAKI = "SDDK"
    GAME_CODE_MILK = "SDDZ"
    GAME_CODE_FINALE = "SDEY"
    GAME_CODE_DX = "SDEZ"
    GAME_CODE_DX_INT = "SDGA"
    GAME_CODE_DX_CN = "SDGB"

    CONFIG_NAME = "mai2.yaml"

    VER_MAIMAI = 0
    VER_MAIMAI_PLUS = 1
    VER_MAIMAI_GREEN = 2
    VER_MAIMAI_GREEN_PLUS = 3
    VER_MAIMAI_ORANGE = 4
    VER_MAIMAI_ORANGE_PLUS = 5
    VER_MAIMAI_PINK = 6
    VER_MAIMAI_PINK_PLUS = 7
    VER_MAIMAI_MURASAKI = 8
    VER_MAIMAI_MURASAKI_PLUS = 9
    VER_MAIMAI_MILK = 10
    VER_MAIMAI_MILK_PLUS = 11
    VER_MAIMAI_FINALE = 12

    VER_MAIMAI_DX = 13
    VER_MAIMAI_DX_PLUS = 14
    VER_MAIMAI_DX_SPLASH = 15
    VER_MAIMAI_DX_SPLASH_PLUS = 16
    VER_MAIMAI_DX_UNIVERSE = 17
    VER_MAIMAI_DX_UNIVERSE_PLUS = 18
    VER_MAIMAI_DX_FESTIVAL = 19
    VER_MAIMAI_DX_FESTIVAL_PLUS = 20
    VER_MAIMAI_DX_BUDDIES = 21
    VER_MAIMAI_DX_BUDDIES_PLUS = 22
    VER_MAIMAI_DX_PRISM = 23
    VER_MAIMAI_DX_PRISM_PLUS = 24
    VER_MAIMAI_DX_CIRCLE = 25

    KALEIDXSCOPE_KEY_CONDITION = {
        1: [
            11009,
            11008,
            11100,
            11097,
            11098,
            11099,
            11163,
            11162,
            11161,
            11228,
            11229,
            11231,
            11463,
            11464,
            11465,
            11538,
            11539,
            11541,
            11620,
            11622,
            11623,
            11737,
            11738,
            11164,
            11230,
            11466,
            11540,
            11621,
            11739,
        ],
        # 青の扉: Played 29 songs
        2: [11102, 11234, 11300, 11529, 11542, 11612],
        # 白の扉: set Frame as "Latent Kingdom" (459504), play 3 or 4 songs by the composer 大国奏音 in 1 pc
        3: [],
        # 紫の扉: JP: need to enter redeem code 51090942171709440000
        4: [
            11023,
            11106,
            11221,
            11222,
            11300,
            11374,
            11458,
            11523,
            11619,
            11663,
            11746,
        ],
        # 黑の扉: Played 11 songs
        5: [
            11003,
            11095,
            11152,
            11224,
            11296,
            11375,
            11452,
            11529,
            11608,
            11669,
            11736,
            11806,
        ],
        # 黄の扉: Use random selection to play one of the songs
        6: [212, 213, 337, 270, 271, 11504, 339, 453, 11336, 11852],
        # 赤の扉: Played 10 songs
        7: [],
        # PRISM TOWER: Get the key after clearing six doors.
        8: [],
        # KALEIDXSCOPE_FIRST_STAGE: Clear Prism Tower
        9: [],
        # 希望の扉: CLEAR KALEIDXSCOPE_FIRST_STAGE
        10: [],
        # KALEIDXSCOPE_SECOND_STAGE: JP: scan the DXPASS of 希望の鍵, will automatically unlock after clearing 希望の扉 in artemis
    }

    VERSION_STRING = (
        "maimai",
        "maimai PLUS",
        "maimai GreeN",
        "maimai GreeN PLUS",
        "maimai ORANGE",
        "maimai ORANGE PLUS",
        "maimai PiNK",
        "maimai PiNK PLUS",
        "maimai MURASAKi",
        "maimai MURASAKi PLUS",
        "maimai MiLK",
        "maimai MiLK PLUS",
        "maimai FiNALE",
        "maimai DX",
        "maimai DX PLUS",
        "maimai DX Splash",
        "maimai DX Splash PLUS",
        "maimai DX UNiVERSE",
        "maimai DX UNiVERSE PLUS",
        "maimai DX FESTiVAL",
        "maimai DX FESTiVAL PLUS",
        "maimai DX BUDDiES",
        "maimai DX BUDDiES PLUS",
        "maimai DX PRiSM",
        "maimai DX PRiSM PLUS",
        "maimai DX CiRCLE",
    )

    @classmethod
    def game_ver_to_string(cls, ver: int):
        return cls.VERSION_STRING[ver]
