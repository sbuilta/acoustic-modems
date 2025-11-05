from __future__ import annotations

from typing import Any

import pytest

from amw.gui import app


def test_main_invokes_app(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}

    class DummyWindow:
        def __init__(self) -> None:
            calls["init"] = True

        def show(self) -> None:
            calls["shown"] = True

    monkeypatch.setattr(app, "MainWindow", DummyWindow)

    def fake_exec(self: app.QApplication) -> int:
        calls["exec"] = True
        return 0

    monkeypatch.setattr(app.QApplication, "exec", fake_exec)
    result = app.main(["--flag"])
    assert result == 0
    assert calls == {"init": True, "exec": True, "shown": True}
