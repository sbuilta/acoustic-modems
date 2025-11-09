"""Helpers for inferring decoded payload formats."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PayloadSummary:
    """Simple description of a decoded payload."""

    guess: str
    preview: str
    length: int
    encoding: str | None = None

    def as_dict(self) -> dict[str, str | int]:
        """Return a JSON-serializable summary payload for metrics display."""
        data: dict[str, str | int] = {
            "payload_guess": self.guess,
            "payload_preview": self.preview,
            "payload_length": self.length,
        }
        if self.encoding:
            data["payload_encoding"] = self.encoding
        data["decode_status"] = "success" if self.length >= 0 else "unknown"
        return data


def summarize_payload(payload: bytes, *, encoding: str = "utf-8") -> PayloadSummary:
    """Attempt to determine whether payload bytes look like text or binary data."""
    length = len(payload)
    if not payload:
        return PayloadSummary(guess="empty", preview="(empty payload)", length=0)

    text_preview = _attempt_text_preview(payload, encoding=encoding)
    if text_preview is not None:
        return PayloadSummary(guess="text", preview=text_preview, length=length, encoding=encoding)

    return PayloadSummary(guess="binary", preview=_binary_preview(payload), length=length)


def _attempt_text_preview(payload: bytes, *, encoding: str) -> str | None:
    """Return a sanitized text preview if the bytes look like UTF text."""
    try:
        decoded = payload.decode(encoding)
    except UnicodeDecodeError:
        return None

    if not decoded:
        return ""

    printable = sum(
        1 for ch in decoded if ch.isprintable() or ch in {"\r", "\n", "\t"}
    )
    ratio = printable / max(len(decoded), 1)
    if ratio < 0.85:
        return None

    sanitized = decoded.replace("\r", "\\r").replace("\n", "\\n")
    if len(sanitized) > 120:
        sanitized = sanitized[:117] + "..."
    return sanitized


def _binary_preview(payload: bytes, *, width: int = 16) -> str:
    """Render a compact hexadecimal preview for binary payloads."""
    slice_ = payload[:width]
    hexed = slice_.hex()
    grouped = " ".join(hexed[i : i + 2] for i in range(0, len(hexed), 2))
    if len(payload) > width:
        grouped += " …"
    return grouped
