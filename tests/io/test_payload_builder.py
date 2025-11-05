from __future__ import annotations

from pathlib import Path

import pytest

from amw.io.payload import PayloadBuilder, PayloadSpec, PayloadType


def test_text_payload_appends_crc() -> None:
    builder = PayloadBuilder()
    spec = PayloadSpec(mode=PayloadType.TEXT, text="hello", crc=True)
    payload = builder.build(spec)
    assert payload[:-4] == b"hello"
    assert len(payload) == len(b"hello") + 4


def test_file_payload_reads_bytes(tmp_path: Path) -> None:
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(b"abc")

    builder = PayloadBuilder()
    spec = PayloadSpec(mode=PayloadType.FILE, file_path=file_path, crc=False)
    payload = builder.build(spec)
    assert payload == b"abc"


def test_file_payload_requires_path() -> None:
    builder = PayloadBuilder()
    spec = PayloadSpec(mode=PayloadType.FILE)
    with pytest.raises(ValueError):
        builder.build(spec)
