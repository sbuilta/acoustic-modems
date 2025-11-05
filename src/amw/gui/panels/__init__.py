"""Panel widgets composing the AMW GUI."""

from .audio_panel import AudioPanel
from .debug_panel import DebugPanel
from .modem_panel import ModemPanel
from .payload_panel import PayloadPanel
from .pipeline_panel import PipelinePanel

__all__ = [
    "AudioPanel",
    "DebugPanel",
    "ModemPanel",
    "PayloadPanel",
    "PipelinePanel",
]
