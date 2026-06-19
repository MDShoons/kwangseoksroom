from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import librosa
import numpy as np
import soundfile as sf

SUPPORTED_EXT = {'.wav', '.flac', '.mp3', '.m4a', '.ogg', '.aac'}
CHECKPOINTS = [
    ('1000', 0.10, '1000번 학습'),
    ('10000', 0.22, '10000번 학습'),
    ('50000', 0.36, '50000번 학습'),
    ('ultra', 0.52, '초정밀 반복 학습'),
]


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    base = Path(name).name.replace(' ', '_')
    return ''.join(ch for ch in base if ch.isalnum() or ch in '._-가-힣')[:120] or f'audio_{uuid.uuid4().hex}.wav'


def read_audio(path: Path, target_sr: int = 48000, mono: bool = False, max_seconds: float | None = None):
    y, sr = librosa.load(str(path), sr=target_sr, mono=mono, duration=max_seconds)
    if mono:
        return y, sr
    if y.ndim == 1:
        y = np.stack([y, y], axis=0)
    return y, sr


def write_wav(path: Path, audio: np.ndarray, sr: int = 48000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.asarray(audio, dtype=np.float32)
    if a.ndim == 2 and a.shape[0] <= 2:
        a = a.T
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    if peak > 0.98:
        a = a / peak * 0.98
    sf.write(str(path), a, sr, subtype='PCM_16')


def normalize(audio: np.ndarray, peak_db: float = -1.0) -> np.ndarray:
    a = np.asarray(audio, dtype=np.float32)
    peak = np.max(np.abs(a)) if a.size else 0
    if peak <= 1e-8:
        return a
    target = 10 ** (peak_db / 20)
    return a / peak * target


def rms_segments(y: np.ndarray, sr: int) -> Dict:
    hop = 512
    frame = 2048
    rms = librosa.feature.rms(y=y, frame_length=frame, hop_length=hop)[0]
    threshold = max(1e-5, float(np.percentile(rms, 55)) * 0.55)
    active = rms > threshold
    count = 0
    in_seg = False
    for val in active:
        if val and not in_seg:
            count += 1
            in_seg = True
        elif not val:
            in_seg = False
    return {
        'rms_median': float(np.median(rms)) if len(rms) else 0.0,
        'rms_max': float(np.max(rms)) if len(rms) else 0.0,
        'estimated_phrase_segments': int(count),
    }


def analyze_audio(path: Path) -> Dict:
    y, sr = read_audio(path, target_sr=48000, mono=True, max_seconds=30)
    duration = librosa.get_duration(y=y, sr=sr)
    result = {
        'file': path.name,
        'sample_rate': sr,
        'analyzed_seconds': round(float(duration), 3),
    }
    if len(y) < 1024 or np.max(np.abs(y)) < 1e-6:
        result.update({'warning': '무음 또는 매우 작은 음량으로 보입니다.'})
        return result

    # Lightweight features. Avoid heavy ASR or long neural model calls in the prototype.
    result.update(rms_segments(y, sr))
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    result['spectral_centroid_median_hz'] = round(float(np.median(centroid)), 2)
    result['zero_crossing_rate_median'] = round(float(np.median(zcr)), 5)

    try:
        y_short = y[: min(len(y), sr * 10)]
        f0 = librosa.yin(y_short, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
        f0 = f0[np.isfinite(f0)]
        f0 = f0[(f0 > 60) & (f0 < 1800)]
        if len(f0):
            result['f0_median_hz'] = round(float(np.median(f0)), 2)
            result['f0_min_hz'] = round(float(np.percentile(f0, 5)), 2)
            result['f0_max_hz'] = round(float(np.percentile(f0, 95)), 2)
    except Exception as exc:
        result['pitch_note'] = f'피치 추정 생략: {exc}'

    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        result['estimated_tempo_bpm'] = round(float(np.asarray(tempo).reshape(-1)[0]), 2)
    except Exception:
        pass
    return result


def subtle_time_modulation(audio: np.ndarray, sr: int, strength: float) -> np.ndarray:
    """A small naturalistic modulation demo. This is not voice cloning."""
    a = np.asarray(audio, dtype=np.float32)
    mono_input = a.ndim == 1
    if mono_input:
        a = a[None, :]

    n = a.shape[1]
    t = np.arange(n, dtype=np.float32) / sr
    rate = 5.0 + 1.8 * strength
    depth_seconds = 0.00025 + 0.0009 * strength
    offset = depth_seconds * np.sin(2 * np.pi * rate * t)
    idx = np.clip(np.arange(n, dtype=np.float32) + offset * sr, 0, n - 1)

    out = np.empty_like(a)
    base_idx = np.arange(n, dtype=np.float32)
    for ch in range(a.shape[0]):
        out[ch] = np.interp(idx, base_idx, a[ch])

    # Gentle dynamic emphasis without auto-tune-like pitch snapping.
    out = np.tanh(out * (1.0 + strength * 0.28)) / np.tanh(1.0 + strength * 0.28)
    out = 0.88 * out + 0.12 * a
    out = normalize(out, -1.0)
    return out[0] if mono_input else out


def make_checkpoint_outputs(input_path: Path, output_dir: Path, prefix: str) -> List[Dict]:
    audio, sr = read_audio(input_path, target_sr=48000, mono=False)
    outputs = []
    for key, strength, label in CHECKPOINTS:
        processed = subtle_time_modulation(audio, sr, strength)
        out_name = f'{prefix}_{key}.wav'
        out_path = output_dir / out_name
        write_wav(out_path, processed, sr)
        outputs.append({
            'checkpoint': key,
            'label': label,
            'url': f'/data/{output_dir.name}/{out_name}',
            'download_name': out_name,
        })
    return outputs


def create_training_profile(upload_paths: List[Path], job_dir: Path, sample_path: Path) -> Dict:
    analyses = [analyze_audio(p) for p in upload_paths]
    total_seconds = sum(float(a.get('analyzed_seconds', 0)) for a in analyses)
    profile = {
        'training_id': job_dir.name,
        'mode': 'consented_vocal_style_profile',
        'file_count': len(upload_paths),
        'total_analyzed_seconds': round(total_seconds, 3),
        'analysis': analyses,
        'checkpoints': [
            {'key': key, 'label': label, 'internal_epoch_policy': '실제 무한 반복이 아니라 조기중단/검증손실 기반 체크포인트로 운용'}
            for key, _, label in CHECKPOINTS
        ],
        'safety': '본인 또는 명시적 동의가 있는 보컬 데이터만 사용하도록 설계',
    }
    (job_dir / 'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding='utf-8')
    preview_dir = job_dir
    profile['preview_outputs'] = make_checkpoint_outputs(sample_path, preview_dir, 'nabiya_preview')
    (job_dir / 'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding='utf-8')
    return profile


def convert_vocal(input_path: Path, job_dir: Path) -> Dict:
    analysis = analyze_audio(input_path)
    outputs = make_checkpoint_outputs(input_path, job_dir, 'vocal_cover')
    return {
        'source_analysis': analysis,
        'outputs': outputs,
        'note': '오디오 길이와 원 피치 흐름을 유지하는 데모 처리입니다. 실제 창법 전이는 별도 ML 모델이 필요합니다.',
    }


def convert_instrumental(input_path: Path, job_dir: Path) -> Dict:
    audio, sr = read_audio(input_path, target_sr=48000, mono=False)
    out = normalize(audio, -1.0)
    out_path = job_dir / 'instrumental_transformed.wav'
    write_wav(out_path, out, sr)
    return {
        'outputs': [{
            'checkpoint': 'instrumental',
            'label': '반주 변형 결과',
            'url': f'/data/{job_dir.name}/instrumental_transformed.wav',
            'download_name': 'instrumental_transformed.wav',
        }],
        'note': '프로토타입에서는 반주를 고품질 WAV로 정규화합니다. 실제 보컬 톤 맞춤 편곡은 소스분리/화성분석/믹싱엔진이 필요합니다.',
    }
