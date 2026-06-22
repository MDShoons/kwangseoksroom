from __future__ import annotations

"""Generate a tiny authorized dummy WAV and run the full scaffold locally.

This demo uses a synthetic sine wave, not a real person's voice.
"""

import json
import math
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def write_demo_wav(path: Path, sr: int = 22050, duration: float = 3.0) -> None:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    f0 = 180 + 2.5 * np.sin(2 * math.pi * 5.0 * t)
    phase = 2 * math.pi * np.cumsum(f0) / sr
    audio = 0.25 * np.sin(phase)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main() -> None:
    vocal = ROOT / "data" / "authorized_vocals" / "synthetic_authorized_demo.wav"
    source = ROOT / "data" / "source_songs" / "example.wav"
    write_demo_wav(vocal)
    write_demo_wav(source, duration=2.0)

    consent = ROOT / "consent.json"
    data = json.loads(consent.read_text(encoding="utf-8"))
    data.update(
        {
            "rights_holder": "Synthetic Demo",
            "vocalist_name_or_alias": "Synthetic Demo Voice",
            "all_singers_consented": True,
            "dataset_is_authorized": True,
        }
    )
    consent.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "make_manifest.py"), "--input", str(ROOT / "data" / "authorized_vocals"), "--output", str(ROOT / "data" / "manifest.json")], env=env)
    subprocess.check_call([sys.executable, "-m", "authorized_vocal_style_ai.train", "--manifest", str(ROOT / "data" / "manifest.json"), "--consent", str(consent), "--output", str(ROOT / "outputs" / "style_profile.json")], cwd=str(ROOT), env=env)
    subprocess.check_call([sys.executable, "-m", "authorized_vocal_style_ai.cover", "--style", str(ROOT / "outputs" / "style_profile.json"), "--source", str(source), "--output", str(ROOT / "outputs" / "demo_vocal_guide.wav")], cwd=str(ROOT), env=env)
    print("Demo complete. Check outputs/.")


if __name__ == "__main__":
    main()
