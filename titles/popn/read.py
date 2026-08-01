import os
import struct
from typing import Dict, List, Optional, Tuple

from core.config import CoreConfig
from read import BaseReader

from .const import PopnConstants
from .database import PopnData


class _PEFile:
    """Small PE address mapper for the offsets used by the Pop'n reader."""

    def __init__(self, data: bytes) -> None:
        if data[:2] != b"MZ":
            raise ValueError("Pop'n music database input is not a PE file")

        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_offset : pe_offset + 4] != b"PE\0\0":
            raise ValueError("Pop'n music database input has no PE header")

        section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
        optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
        optional_offset = pe_offset + 24
        magic = struct.unpack_from("<H", data, optional_offset)[0]
        if magic == 0x10B:
            self.image_base = struct.unpack_from("<I", data, optional_offset + 28)[0]
        elif magic == 0x20B:
            self.image_base = struct.unpack_from("<Q", data, optional_offset + 24)[0]
        else:
            raise ValueError("Pop'n music database input has an unknown PE format")

        section_offset = optional_offset + optional_size
        self.sections: List[Tuple[int, int, int, int]] = []
        for index in range(section_count):
            current = section_offset + (index * 40)
            virtual_size, virtual_address = struct.unpack_from("<II", data, current + 8)
            raw_size, raw_offset = struct.unpack_from("<II", data, current + 16)
            self.sections.append(
                (virtual_address, max(virtual_size, raw_size), raw_offset, raw_size)
            )

    def virtual_to_physical(self, offset: int) -> int:
        for virtual_address, size, raw_offset, raw_size in self.sections:
            start = self.image_base + virtual_address
            if start <= offset < start + size:
                physical = raw_offset + (offset - start)
                if physical >= raw_offset + raw_size:
                    raise ValueError(f"Virtual offset 0x{offset:08x} is outside raw data")
                return physical
        raise ValueError(f"Virtual offset 0x{offset:08x} is not in a PE section")


class PopnReader(BaseReader):
    """Import Pop'n chart metadata using bemaniutils' M39 database layout."""

    MUSIC_OFFSET = 0x2C5510
    MUSIC_STEP = 172
    MUSIC_LENGTH = 2189
    FILE_OFFSET = 0x2B2F28
    FILE_STEP = 32
    MODERN_MUSIC_OFFSET = 0x78A020
    MODERN_MUSIC_STEP = 0x138
    # The High☆Cheers table is followed immediately by unrelated DLL data.
    # Do not scan the rest of the image as if it were music records.
    MODERN_MUSIC_MAX = 626
    ACCENT_LUT = {
        "鵝": "7",
        "圄": "à",
        "圉": "ä",
        "鵤": "Ä",
        "鶸": "á",
        "鵑": "👁",
        "鶤": "©",
        "圈": "é",
        "鵐": "ê",
        "鵙": "Ə",
        "鵲": "ë",
        "！": "!",
        "囿": "♥",
        "鶚": "㊙",
        "鶉": "ó",
        "鶇": "ö",
        "鶲": "Ⓟ",
        "鶫": "²",
        "鷆": "ř",
        "鷏": "í",
        "圍": "@",
        "圖": "ţ",
        "鵺": "Ü",
        "鶺": "Ú",
        "囎": "⧗",
        "囂": "♡",
        "佰": "你",
        "釁": "🐾",
        "炙": "焱",
        "罕": "έ",
        "罔": "ς",
        "冫": "ꓘ",
        "彑": "Ø",
        "暠": "Ⓤ",
        "[/c][c:FF6d6d]Ⓤ[/c]": "Ⓤ",
        "[/c][c:FF6d6d]鉑[/c]": "",
    }

    def __init__(
        self,
        config: CoreConfig,
        version: int,
        bin_dir: Optional[str],
        opt_dir: Optional[str],
        extra: Optional[str],
    ) -> None:
        super().__init__(config, version, bin_dir, opt_dir, extra)
        self.data = PopnData(config)

        try:
            self.logger.info(
                f"Start importer for {PopnConstants.game_ver_to_string(version)}"
            )
        except IndexError:
            self.logger.error(f"Invalid Pop'n version {version}")
            exit(1)

    async def read(self) -> None:
        binaries = self._find_binaries()
        if not binaries:
            self.logger.error(
                "Pop'n reader requires --binfolder to point to the M39 executable or MDB"
            )
            return

        for binary in binaries:
            for song in self._scrape(binary):
                if (
                    song["title"] in ["-", "‐"]
                    and song["genre"] in ["-", "‐"]
                    and song["artist"] in ["-", "‐"]
                    and song["comment"] in ["-", "‐"]
                ):
                    continue
                if (
                    song["title"] == "ＤＵＭＭＹ"
                    and song["artist"] == "ＤＵＭＭＹ"
                    and song["genre"] == "ＤＵＭＭＹ"
                ):
                    continue

                title = song["title_en"] or song["title"]
                artist = song["artist_en"] or song["artist"]
                for chart_id, difficulty in enumerate(song["difficulty"]):
                    result = await self.data.static.put_music(
                        self.version,
                        song["id"],
                        chart_id,
                        title,
                        artist,
                        song["genre"],
                        str(song["folder"]),
                        difficulty,
                    )
                    if result is not None:
                        self.logger.info(
                            "Imported song %s chart %s: %s",
                            song["id"],
                            chart_id,
                            title,
                        )
                    else:
                        self.logger.warning(
                            "Failed to import song %s chart %s: %s",
                            song["id"],
                            chart_id,
                            title,
                        )

    def _find_binaries(self) -> List[str]:
        binaries = []
        for candidate in (self.bin_dir, self.extra):
            if candidate is not None and os.path.isfile(candidate):
                binaries.append(candidate)
        if self.opt_dir is not None and os.path.isfile(self.opt_dir):
            binaries.append(self.opt_dir)
        return list(dict.fromkeys(binaries))

    def _scrape(self, filename: str) -> List[Dict[str, object]]:
        with open(filename, "rb") as handle:
            data = handle.read()
        pe = _PEFile(data) if data[:2] == b"MZ" else None

        mdb = self._scrape_mdb(data, pe)
        if mdb:
            return mdb
        if pe is None:
            raise ValueError("Pop'n music database input is not a supported PE or MDB file")

        def read_string(pointer: int) -> str:
            if pointer == 0:
                return ""
            offset = pe.virtual_to_physical(pointer)
            end = data.index(b"\0", offset)
            return data[offset:end].decode("cp932")

        modern = self._scrape_modern(data, pe, read_string)
        if modern:
            return modern

        return self._scrape_legacy(data, pe, read_string)

    def _scrape_mdb(self, data: bytes, pe: Optional[_PEFile]) -> List[Dict[str, object]]:
        """Read the 312-byte High☆Cheers music database records."""

        marker = bytes.fromhex(
            "1c001d00000008070100000000000000000000030e1326"
        )
        marker_offset = data.find(marker)
        if marker_offset < 0:
            return []

        offset = marker_offset - 0x38
        step = 312
        record_format = "<" + "Q" * 7 + "H" * 2 + "I" * 4 + "B" * 8 + "xx" + "H" * 6
        record_size = struct.calcsize(record_format)
        if offset < 0 or offset + record_size > len(data):
            return []

        length = 0
        check_offset = 8
        while offset + ((length + 1) * step) <= len(data):
            check = offset + ((length + 1) * step) - check_offset
            if data[check : check + 1] != b"\0":
                break
            length += 1
        if length == 0:
            return []

        def read_string(pointer: int) -> str:
            if pointer == 0:
                return ""
            try:
                string_offset = pe.virtual_to_physical(pointer) if pe is not None else pointer
            except ValueError:
                string_offset = pointer
            if string_offset < 0 or string_offset >= len(data):
                raise ValueError(f"MDB string offset 0x{pointer:x} is out of range")
            end = data.index(b"\0", string_offset)
            return data[string_offset:end].decode("cp932")

        songs: List[Dict[str, object]] = []
        music_id = 0
        for _ in range(length):
            values = struct.unpack_from(record_format, data, offset)
            pointers = values[:7]
            chart_mask = values[9]
            difficulties = values[13:17]
            try:
                title = read_string(pointers[1])
                artist = read_string(pointers[2])
                genre = read_string(pointers[0])
                title_en = read_string(pointers[5])
                artist_en = read_string(pointers[6])
                comment = read_string(pointers[4])
            except (ValueError, UnicodeDecodeError):
                offset += step
                music_id += 1
                continue

            songs.append(self._fix_song_text({
                "id": music_id,
                "genre": genre,
                "title": title,
                "artist": artist,
                "comment": comment,
                "title_en": title_en,
                "artist_en": artist_en,
                "folder": values[10],
                "difficulty": [
                    difficulties[0] if chart_mask & 0x0080000 else 0,
                    difficulties[1],
                    difficulties[2] if chart_mask & 0x1000000 else 0,
                    difficulties[3] if chart_mask & 0x2000000 else 0,
                ],
            }))
            offset += step
            music_id += 1

        return songs

    def _scrape_modern(
        self, data: bytes, pe: _PEFile, read_string
    ) -> List[Dict[str, object]]:
        songs: List[Dict[str, object]] = []

        for song_index in range(self.MODERN_MUSIC_MAX):
            offset = self.MODERN_MUSIC_OFFSET + (self.MODERN_MUSIC_STEP * song_index)
            if offset + self.MODERN_MUSIC_STEP > len(data):
                break

            pointers = struct.unpack_from("<7Q", data, offset)
            valid_pointers = 0
            invalid_pointer = False
            for pointer in pointers:
                if pointer == 0:
                    valid_pointers += 1
                    continue
                try:
                    pe.virtual_to_physical(pointer)
                    valid_pointers += 1
                except ValueError:
                    invalid_pointer = True

            if invalid_pointer or valid_pointers < 6:
                break

            packed_id = struct.unpack_from("<I", data, offset + 0x38)[0]
            difficulties = struct.unpack_from("<4B", data, offset + 0x4C)
            try:
                song = self._fix_song_text(
                    {
                        "id": packed_id & 0xFFFF,
                        # High☆Cheers records use the same field order as the
                        # extracted MDB parser: genre, title, artist, long
                        # genre, comment, English title, English artist.
                        "genre": read_string(pointers[0]),
                        "title": read_string(pointers[1]),
                        "artist": read_string(pointers[2]),
                        "comment": read_string(pointers[4]),
                        "title_en": read_string(pointers[5]),
                        "artist_en": read_string(pointers[6]),
                        "folder": struct.unpack_from("<I", data, offset + 0x3C)[0],
                        "difficulty": list(difficulties),
                    }
                )
                # Empty records are table padding, not playable songs.
                if not song["title"] and not song["artist"] and not song["genre"]:
                    continue
                if not any(song["difficulty"]):
                    continue
                songs.append(song)
            except (ValueError, UnicodeDecodeError):
                continue

        return songs

    def _scrape_legacy(
        self, data: bytes, pe: _PEFile, read_string
    ) -> List[Dict[str, object]]:
        def available_charts(mask: int) -> Tuple[bool, bool, bool, bool]:
            return (True, True, bool(mask & 0x1000000), bool(mask & 0x2000000))

        songs: List[Dict[str, object]] = []
        for song_id in range(self.MUSIC_LENGTH):
            offset = self.MUSIC_OFFSET + (self.MUSIC_STEP * song_id)
            values = struct.unpack_from(
                "<IIIIIIHHIIII6B2x6H108x", data, offset
            )
            charts = available_charts(values[8])
            songs.append(self._fix_song_text({
                    "id": song_id,
                    "genre": read_string(values[0]),
                    "title": read_string(values[1]),
                    "artist": read_string(values[2]),
                    "comment": read_string(values[3]),
                    "title_en": read_string(values[4]),
                    "artist_en": read_string(values[5]),
                    "folder": values[9],
                    "difficulty": [
                        values[12] if charts[0] else 0,
                        values[13] if charts[1] else 0,
                        values[14] if charts[2] else 0,
                        values[15] if charts[3] else 0,
                    ],
                }))
        return songs

    @classmethod
    def _fix_song_text(cls, song: Dict[str, object]) -> Dict[str, object]:
        for field in ("genre", "title", "artist", "comment", "title_en", "artist_en"):
            value = song[field]
            if isinstance(value, str):
                for original, replacement in cls.ACCENT_LUT.items():
                    value = value.replace(original, replacement)
                song[field] = value
        return song
