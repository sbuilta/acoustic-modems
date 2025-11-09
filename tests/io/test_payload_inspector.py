from __future__ import annotations

from amw.io.payload_inspector import summarize_payload


def test_summarize_payload_detects_text() -> None:
    summary = summarize_payload("Hello modem!".encode("utf-8")).as_dict()
    assert summary["payload_guess"] == "text"
    assert "Hello" in summary["payload_preview"]
    assert summary["payload_length"] == len("Hello modem!".encode("utf-8"))


def test_summarize_payload_handles_binary() -> None:
    payload = bytes(range(32))
    summary = summarize_payload(payload).as_dict()
    assert summary["payload_guess"] == "binary"
    assert summary["payload_preview"].startswith("00 01")


def test_summarize_payload_handles_empty() -> None:
    summary = summarize_payload(b"").as_dict()
    assert summary["payload_guess"] == "empty"
    assert summary["payload_preview"] == "(empty payload)"
