"""Payload helpers for building modem inputs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PayloadType(str, Enum):
    """Supported payload modes."""

    TEXT = "text"
    FILE = "file"


@dataclass(slots=True)
class PayloadSpec:
    """Definition for the payload to transmit."""

    mode: PayloadType
    text: str = ""
    file_path: Path | None = None
    crc: bool = True
    encoding: str = "utf-8"


class PayloadBuilder:
    """Converts payload specs into byte buffers."""

    def build(self, spec: PayloadSpec) -> bytes:
        if spec.mode is PayloadType.TEXT:
            payload = spec.text.encode(spec.encoding)
        else:
            if not spec.file_path:
                raise ValueError("PayloadSpec requires file_path when mode=FILE.")
            payload = Path(spec.file_path).read_bytes()

        if spec.crc:
            payload = self._append_crc32(payload)
        return payload

    @staticmethod
    def _append_crc32(payload: bytes) -> bytes:
        import zlib

        checksum = zlib.crc32(payload) & 0xFFFFFFFF
        return payload + checksum.to_bytes(4, byteorder="big")
