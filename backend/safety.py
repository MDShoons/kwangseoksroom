from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ALLOWED_AUDIO_EXTENSIONS = {".wav"}
MAX_FILE_BYTES = 250 * 1024 * 1024  # 250 MB per file for the prototype

BLOCKED_PHRASES = {
    "무단복제",
    "사칭",
    "유명가수 모창",
    "권리자 허락 없음",
    "동의 없음",
}

@dataclass(frozen=True)
class SafetyCheck:
    ok: bool
    message: str


def validate_audio_filename(filename: str) -> SafetyCheck:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        return SafetyCheck(False, "현재 프로토타입은 PCM WAV 파일만 허용합니다. MP3는 WAV로 변환 후 업로드하세요.")
    return SafetyCheck(True, "ok")


def validate_consent_fields(
    *,
    rights_holder: str,
    vocalist_name_or_alias: str,
    all_singers_consented: bool,
    dataset_is_authorized: bool,
    no_impersonation: bool,
    ai_disclosure_agreed: bool,
) -> SafetyCheck:
    if not rights_holder.strip():
        return SafetyCheck(False, "권리자/동의권자 이름을 입력해야 합니다.")
    if not vocalist_name_or_alias.strip():
        return SafetyCheck(False, "보컬 제공자 이름 또는 별칭을 입력해야 합니다.")
    if not all_singers_consented:
        return SafetyCheck(False, "모든 보컬 제공자의 명시적 동의가 확인되어야 합니다.")
    if not dataset_is_authorized:
        return SafetyCheck(False, "업로드 음원의 학습·분석 사용 권한이 확인되어야 합니다.")
    if not no_impersonation:
        return SafetyCheck(False, "실존 인물 사칭·무단 모창·상업 배포 금지에 동의해야 합니다.")
    if not ai_disclosure_agreed:
        return SafetyCheck(False, "결과물에 AI 합성/연구용 데모임을 표시하는 데 동의해야 합니다.")
    joined = " ".join([rights_holder, vocalist_name_or_alias]).lower()
    for phrase in BLOCKED_PHRASES:
        if phrase.lower() in joined:
            return SafetyCheck(False, "권리 확인이 불분명한 사칭/무단복제 목적 문구가 포함되어 있습니다.")
    return SafetyCheck(True, "ok")


def enforce_file_count(files: Iterable[object], max_count: int = 10) -> SafetyCheck:
    count = len(list(files))
    if count == 0:
        return SafetyCheck(False, "최소 1개의 학습용 WAV 파일을 업로드해야 합니다.")
    if count > max_count:
        return SafetyCheck(False, f"학습용 파일은 최대 {max_count}개까지만 허용합니다.")
    return SafetyCheck(True, "ok")
