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
                "Pop'n reader requires --binfolder to point to the M39 executable"
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
                    await self.data.static.put_music(
                        self.version,
                        song["id"],
                        chart_id,
                        title,
                        artist,
                        song["genre"],
                        str(song["folder"]),
                        difficulty,
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
        pe = _PEFile(data)

        def read_string(pointer: int) -> str:
            offset = pe.virtual_to_physical(pointer)
            end = data.index(b"\0", offset)
            return data[offset:end].decode("shift_jisx0213")

        def available_charts(mask: int) -> Tuple[bool, bool, bool, bool]:
            return (True, True, bool(mask & 0x1000000), bool(mask & 0x2000000))

        songs: List[Dict[str, object]] = []
        for song_id in range(self.MUSIC_LENGTH):
            offset = self.MUSIC_OFFSET + (self.MUSIC_STEP * song_id)
            values = struct.unpack_from(
                "<IIIIIIHHIIII6B2x6H108x", data, offset
            )
            charts = available_charts(values[8])
            songs.append(
                {
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
                }
            )
        return songs
