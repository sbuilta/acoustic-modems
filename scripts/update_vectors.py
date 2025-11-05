"""Regenerate golden vector WAV files for regression testing."""

from __future__ import annotations

from pathlib import Path

from loguru import logger


def update_vectors(output_dir: Path | None = None) -> None:
    """Placeholder for future automation."""
    target = Path(output_dir or Path(__file__).resolve().parents[1] / "tests" / "data" / "golden_vectors")
    target.mkdir(parents=True, exist_ok=True)
    logger.info("Golden vectors should be regenerated using real modem pipelines.")


if __name__ == "__main__":
    update_vectors()
