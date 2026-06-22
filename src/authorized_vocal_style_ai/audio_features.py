from __future__ import annotations

import math
import wave
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np


@dataclass
class VocalFeatureSummary:
    file: str
    duration_sec: float
    sample_rate: int
    rms_mean: float
    rms_std: float
    zero_crossing_rate: float
    pitch_proxy_hz: float
    vibrato_proxy: float
    breathiness_proxy: float
    attack_proxy: float

    def to_dict(self) -> Dict[str, float | int | str]:
        return asdict(self)


def read_wav_mono(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a PCM WAV file with stdlib wave and return mono float32 audio."""
    path = Path(path)
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    if sample_width == 1:
        data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 4:
        data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width}")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    return data.astype(np.float32), sample_rate


def frame_audio(x: np.ndarray, frame_size: int, hop_size: int) -> np.ndarray:
    if len(x) < frame_size:
        return x.reshape(1, -1)
    frames = []
    for start in range(0, len(x) - frame_size + 1, hop_size):
        frames.append(x[start : start + frame_size])
    return np.stack(frames, axis=0)


def rms(frames: np.ndarray) -> np.ndarray:
    return np.sqrt(np.mean(frames * frames, axis=1) + 1e-9)


def zero_crossing_rate(x: np.ndarray) -> float:
    if len(x) < 2:
        return 0.0
    signs = np.signbit(x)
    return float(np.mean(signs[1:] != signs[:-1]))


def autocorr_pitch_proxy(frame: np.ndarray, sr: int, fmin: float = 70.0, fmax: float = 900.0) -> float:
    """Rough monophonic pitch proxy. This is not a production-grade F0 extractor."""
    if np.max(np.abs(frame)) < 1e-4:
        return 0.0
    frame = frame - np.mean(frame)
    corr = np.correlate(frame, frame, mode="full")[len(frame)-1:]
    min_lag = max(1, int(sr / fmax))
    max_lag = min(len(corr) - 1, int(sr / fmin))
    if max_lag <= min_lag:
        return 0.0
    lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
    if lag <= 0:
        return 0.0
    return float(sr / lag)


def summarize_wav(path: str | Path, frame_ms: int = 40, hop_ms: int = 10) -> VocalFeatureSummary:
    x, sr = read_wav_mono(path)
    duration = len(x) / float(sr) if sr else 0.0
    frame_size = max(1, int(sr * frame_ms / 1000))
    hop_size = max(1, int(sr * hop_ms / 1000))
    frames = frame_audio(x, frame_size, hop_size)
    energy = rms(frames)

    pitch_values: List[float] = []
    for fr, e in zip(frames, energy):
        if e > max(0.01, float(np.percentile(energy, 40))):
            p = autocorr_pitch_proxy(fr, sr)
            if 50.0 <= p <= 1000.0:
                pitch_values.append(p)

    pitch_proxy = float(np.median(pitch_values)) if pitch_values else 0.0
    vibrato_proxy = float(np.std(np.diff(pitch_values))) if len(pitch_values) > 2 else 0.0
    zcr = zero_crossing_rate(x)
    breathiness_proxy = float(zcr / (float(np.mean(energy)) + 1e-6))

    # Attack proxy: how quickly energy rises in the first voiced frames.
    voiced_energy = energy[energy > max(0.01, np.percentile(energy, 50))]
    if len(voiced_energy) > 3:
        attack_proxy = float(np.max(np.diff(voiced_energy[: min(20, len(voiced_energy))])))
    else:
        attack_proxy = 0.0

    return VocalFeatureSummary(
        file=str(path),
        duration_sec=round(duration, 3),
        sample_rate=sr,
        rms_mean=float(np.mean(energy)),
        rms_std=float(np.std(energy)),
        zero_crossing_rate=zcr,
        pitch_proxy_hz=pitch_proxy,
        vibrato_proxy=vibrato_proxy,
        breathiness_proxy=breathiness_proxy,
        attack_proxy=attack_proxy,
    )


def aggregate_features(features: Iterable[VocalFeatureSummary]) -> Dict[str, float | int | List[Dict[str, float | int | str]]]:
    items = list(features)
    if not items:
        raise ValueError("No WAV features found. Add authorized WAV files to data/authorized_vocals.")
    numeric_keys = [
        "duration_sec",
        "rms_mean",
        "rms_std",
        "zero_crossing_rate",
        "pitch_proxy_hz",
        "vibrato_proxy",
        "breathiness_proxy",
        "attack_proxy",
    ]
    aggregate: Dict[str, float | int | List[Dict[str, float | int | str]]] = {
        "file_count": len(items),
        "files": [item.to_dict() for item in items],
    }
    for key in numeric_keys:
        values = [float(getattr(item, key)) for item in items]
        aggregate[f"{key}_mean"] = float(np.mean(values))
        aggregate[f"{key}_std"] = float(np.std(values))
    return aggregate
