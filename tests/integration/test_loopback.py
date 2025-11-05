from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Hardware loopback scenario not implemented yet")
def test_loopback_placeholder() -> None:
    pass
