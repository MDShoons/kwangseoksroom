from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .audio_engine import (
    SUPPORTED_EXT,
    convert_instrumental,
    convert_vocal,
    create_training_profile,
    ensure_dirs,
    safe_filename,
)

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / 'static'
DATA_DIR = ROOT / 'data'
SAMPLE_PATH = ROOT / 'samples' / 'nabiya.wav'
MAX_TRAIN_FILES = 10
MAX_TRAIN_TOTAL_BYTES = 5 * 1024 ** 3
MAX_SINGLE_COVER_BYTES = 1 * 1024 ** 3

ensure_dirs(DATA_DIR)

app = FastAPI(title='Mochang AI Prototype', version='0.1.0')
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')
app.mount('/data', StaticFiles(directory=str(DATA_DIR)), name='data')


@app.get('/')
def index():
    return FileResponse(STATIC_DIR / 'index.html')


def validate_audio_file(file: UploadFile) -> None:
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f'지원하지 않는 파일 형식입니다: {suffix}')


def save_upload(file: UploadFile, dst_dir: Path) -> Path:
    validate_audio_file(file)
    path = dst_dir / safe_filename(file.filename or f'audio_{uuid.uuid4().hex}.wav')
    with path.open('wb') as f:
        shutil.copyfileobj(file.file, f)
    return path


@app.post('/api/train')
def train(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail='학습할 보컬 파일을 업로드하세요.')
    if len(files) > MAX_TRAIN_FILES:
        raise HTTPException(status_code=400, detail='학습 파일은 최대 10개까지 가능합니다.')

    total = 0
    for file in files:
        validate_audio_file(file)
        size = int(file.headers.get('content-length') or 0)
        total += size
    if total > MAX_TRAIN_TOTAL_BYTES:
        raise HTTPException(status_code=400, detail='학습 파일 총 용량은 5GB를 넘을 수 없습니다.')

    job_dir = DATA_DIR / f'train_{uuid.uuid4().hex[:12]}'
    ensure_dirs(job_dir)
    paths = [save_upload(file, job_dir) for file in files]
    profile = create_training_profile(paths, job_dir, SAMPLE_PATH)
    return profile


@app.post('/api/convert-vocal')
def convert_vocal_api(file: UploadFile = File(...)):
    validate_audio_file(file)
    size = int(file.headers.get('content-length') or 0)
    if size > MAX_SINGLE_COVER_BYTES:
        raise HTTPException(status_code=400, detail='보컬변환 파일은 1GB 이하만 가능합니다.')
    job_dir = DATA_DIR / f'cover_{uuid.uuid4().hex[:12]}'
    ensure_dirs(job_dir)
    path = save_upload(file, job_dir)
    return convert_vocal(path, job_dir)


@app.post('/api/convert-instrumental')
def convert_instrumental_api(file: UploadFile = File(...)):
    validate_audio_file(file)
    job_dir = DATA_DIR / f'inst_{uuid.uuid4().hex[:12]}'
    ensure_dirs(job_dir)
    path = save_upload(file, job_dir)
    return convert_instrumental(path, job_dir)
