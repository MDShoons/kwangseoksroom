from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def write_metadata(output_audio_path: str | Path, metadata: Dict[str, Any]) -> Path:
    """Write a sidecar metadata file for an AI-generated output."""
    output_audio_path = Path(output_audio_path)
    sidecar = output_audio_path.with_suffix(output_audio_path.suffix + ".metadata.json")
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_audio": str(output_audio_path),
        "ai_synthesized": True,
        "metadata": metadata,
    }
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return sidecar
