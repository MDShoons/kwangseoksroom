from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from authorized_vocal_style_ai.cover import synthesize_research_vocal_guide
from authorized_vocal_style_ai.train import train_style_profile
from backend.safety import (
    MAX_FILE_BYTES,
    enforce_file_count,
    validate_audio_filename,
    validate_consent_fields,
)

APP_TITLE = "Authorized Vocal Style AI Site"
UPLOAD_DIR = ROOT / "uploads"
OUTPUT_DIR = ROOT / "outputs"
FRONTEND_DIR = ROOT / "frontend" / "static"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def make_job_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def save_upload(upload: UploadFile, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with target.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_BYTES:
                raise HTTPException(status_code=413, detail=f"파일이 너무 큽니다: {upload.filename}")
            out.write(chunk)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "title": APP_TITLE,
        "mode": "consent_based_research_prototype",
        "notice": "This site blocks training unless authorization and disclosure checks are completed.",
    }


@app.post("/api/train")
def train_authorized_style(
    rights_holder: str = Form(...),
    vocalist_name_or_alias: str = Form(...),
    project_name: str = Form("Authorized Vocal Style AI Site Demo"),
    all_singers_consented: bool = Form(False),
    dataset_is_authorized: bool = Form(False),
    no_impersonation: bool = Form(False),
    ai_disclosure_agreed: bool = Form(False),
    files: List[UploadFile] = File(...),
) -> dict:
    consent_check = validate_consent_fields(
        rights_holder=rights_holder,
        vocalist_name_or_alias=vocalist_name_or_alias,
        all_singers_consented=all_singers_consented,
        dataset_is_authorized=dataset_is_authorized,
        no_impersonation=no_impersonation,
        ai_disclosure_agreed=ai_disclosure_agreed,
    )
    if not consent_check.ok:
        raise HTTPException(status_code=400, detail=consent_check.message)

    count_check = enforce_file_count(files, max_count=10)
    if not count_check.ok:
        raise HTTPException(status_code=400, detail=count_check.message)

    job_id = make_job_id()
    job_upload_dir = UPLOAD_DIR / job_id / "authorized_vocals"
    job_output_dir = OUTPUT_DIR / job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir.mkdir(parents=True, exist_ok=True)

    manifest_files = []
    for idx, upload in enumerate(files, start=1):
        filename = upload.filename or f"vocal_{idx}.wav"
        filename_check = validate_audio_filename(filename)
        if not filename_check.ok:
            raise HTTPException(status_code=400, detail=f"{filename}: {filename_check.message}")
        target = job_upload_dir / f"{idx:02d}_{Path(filename).name}"
        save_upload(upload, target)
        manifest_files.append({"path": str(target)})

    manifest_path = job_output_dir / "manifest.json"
    manifest_path.write_text(json.dumps({"files": manifest_files}, ensure_ascii=False, indent=2), encoding="utf-8")

    consent = {
        "project_name": project_name,
        "rights_holder": rights_holder,
        "vocalist_name_or_alias": vocalist_name_or_alias,
        "all_singers_consented": all_singers_consented,
        "dataset_is_authorized": dataset_is_authorized,
        "allowed_use": ["research", "internal_demo", "authorized_web_demo"],
        "prohibited_use": [
            "unauthorized_real_person_voice_clone",
            "impersonation",
            "commercial_release_without_contract",
            "misleading_public_distribution",
        ],
        "disclosure_text": "AI synthesized vocal demo created from authorized data; not a live human performance.",
        "consent_document_path": "consent_template.md",
    }
    consent_path = job_output_dir / "consent.json"
    consent_path.write_text(json.dumps(consent, ensure_ascii=False, indent=2), encoding="utf-8")

    style_path = job_output_dir / "style_profile.json"
    try:
        train_style_profile(manifest_path, consent_path, style_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"학습 프로파일 생성 실패: {exc}") from exc

    return {
        "ok": True,
        "job_id": job_id,
        "message": "동의 기반 보컬 스타일 프로파일이 생성되었습니다.",
        "style_profile_url": f"/api/jobs/{job_id}/style-profile",
        "next_step": "커버/가이드 생성 영역에서 변환할 WAV 파일을 업로드하세요.",
    }


@app.post("/api/cover/{job_id}")
def cover_authorized_style(job_id: str, source_song: UploadFile = File(...)) -> dict:
    style_path = OUTPUT_DIR / job_id / "style_profile.json"
    if not style_path.exists():
        raise HTTPException(status_code=404, detail="해당 job_id의 스타일 프로파일을 찾을 수 없습니다. 먼저 학습을 실행하세요.")

    filename = source_song.filename or "source_song.wav"
    filename_check = validate_audio_filename(filename)
    if not filename_check.ok:
        raise HTTPException(status_code=400, detail=filename_check.message)

    job_upload_dir = UPLOAD_DIR / job_id / "source_songs"
    job_upload_dir.mkdir(parents=True, exist_ok=True)
    source_path = job_upload_dir / Path(filename).name
    save_upload(source_song, source_path)

    output_path = OUTPUT_DIR / job_id / "research_vocal_guide.wav"
    try:
        synthesize_research_vocal_guide(style_path, source_path, output_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"가이드 생성 실패: {exc}") from exc

    return {
        "ok": True,
        "job_id": job_id,
        "message": "연구용 보컬 가이드 WAV가 생성되었습니다. 실제 가수 목소리 복제물이 아닙니다.",
        "audio_url": f"/api/jobs/{job_id}/audio",
        "metadata_url": f"/api/jobs/{job_id}/metadata",
    }


@app.get("/api/jobs/{job_id}/style-profile")
def download_style_profile(job_id: str) -> FileResponse:
    path = OUTPUT_DIR / job_id / "style_profile.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="style_profile.json을 찾을 수 없습니다.")
    return FileResponse(path, filename="style_profile.json", media_type="application/json")


@app.get("/api/jobs/{job_id}/audio")
def download_audio(job_id: str) -> FileResponse:
    path = OUTPUT_DIR / job_id / "research_vocal_guide.wav"
    if not path.exists():
        raise HTTPException(status_code=404, detail="research_vocal_guide.wav를 찾을 수 없습니다.")
    return FileResponse(path, filename="research_vocal_guide.wav", media_type="audio/wav")


@app.get("/api/jobs/{job_id}/metadata")
def get_metadata(job_id: str) -> dict:
    meta_path = OUTPUT_DIR / job_id / "research_vocal_guide.wav.meta.json"
    style_path = OUTPUT_DIR / job_id / "style_profile.json"
    result = {}
    if style_path.exists():
        result["style_profile"] = json.loads(style_path.read_text(encoding="utf-8"))
    if meta_path.exists():
        result["audio_metadata"] = json.loads(meta_path.read_text(encoding="utf-8"))
    if not result:
        raise HTTPException(status_code=404, detail="metadata를 찾을 수 없습니다.")
    return result


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str) -> dict:
    for base in [UPLOAD_DIR, OUTPUT_DIR]:
        target = base / job_id
        if target.exists():
            shutil.rmtree(target)
    return {"ok": True, "message": "해당 작업 파일을 삭제했습니다."}
