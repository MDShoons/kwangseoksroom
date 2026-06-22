from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

import numpy as np

from .watermark import write_metadata


def write_wav(path: str | Path, audio: np.ndarray, sr: int = 22050) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def synthesize_research_vocal_guide(style_profile_path: str | Path, source_path: str | Path, output_path: str | Path) -> Path:
    """Create a transparent non-impersonating guide tone from the style profile.

    This function intentionally does NOT generate a real person's voice. It creates a
    simple audible guide demonstrating how a style profile could modulate pitch,
    vibrato, attack, and breath-like noise in a future consent-based synthesizer.
    """
    profile = json.loads(Path(style_profile_path).read_text(encoding="utf-8"))
    features = profile["style_features"]
    sr = 22050
    duration = min(8.0, max(2.5, float(features.get("duration_sec_mean", 4.0))))
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    base_pitch = float(features.get("pitch_proxy_hz_mean", 220.0)) or 220.0
    vibrato = min(8.0, max(0.2, float(features.get("vibrato_proxy_mean", 1.5)) / 8.0))
    breath = min(0.08, max(0.005, float(features.get("breathiness_proxy_mean", 0.02)) * 0.0005))
    attack = min(0.3, max(0.03, float(features.get("attack_proxy_mean", 0.05))))

    f0 = base_pitch + (vibrato * np.sin(2 * math.pi * 5.2 * t))
    phase = 2 * math.pi * np.cumsum(f0) / sr
    tone = 0.25 * np.sin(phase)

    envelope = np.ones_like(tone)
    attack_samples = max(1, int(sr * attack))
    envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)
    release_samples = max(1, int(sr * 0.25))
    envelope[-release_samples:] = np.linspace(1.0, 0.0, release_samples)

    rng = np.random.default_rng(42)
    noise = breath * rng.normal(0, 1, size=tone.shape)
    audio = (tone * envelope) + noise

    output = Path(output_path)
    write_wav(output, audio, sr=sr)
    write_metadata(
        output,
        {
            "source_song_reference": str(source_path),
            "style_profile": str(style_profile_path),
            "disclosure": profile.get("consent_metadata", {}).get("disclosure_text", "AI synthesized demo."),
            "notice": "Guide tone only; not a real-person vocal clone.",
        },
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a non-impersonating research vocal guide.")
    parser.add_argument("--style", required=True, help="Path to outputs/style_profile.json")
    parser.add_argument("--source", required=True, help="Source song path, used only as metadata in this scaffold")
    parser.add_argument("--output", required=True, help="Output WAV path")
    args = parser.parse_args()
    out = synthesize_research_vocal_guide(args.style, args.source, args.output)
    print(f"Saved research guide WAV: {out}")


if __name__ == "__main__":
    main()
