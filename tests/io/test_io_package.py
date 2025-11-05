from __future__ import annotations

import amw.io as io_pkg
from amw.io import audio, payload


def test_io_package_lazy_exports() -> None:
    assert io_pkg.AudioService is audio.AudioService
    assert io_pkg.PayloadBuilder is payload.PayloadBuilder
