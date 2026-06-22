# Authorized Vocal Style AI Prototype

이 ZIP은 **권리자와 보컬 당사자의 명시적 동의를 받은 음성 데이터만** 사용하도록 설계한 연구용 프로토타입입니다.  
실존 가수·성우·일반인의 목소리를 허락 없이 복제하거나, 특정 인물인 것처럼 들리게 만들어 배포하는 용도로 사용할 수 없습니다.

## 목표

사용자가 제공한 합법적 보컬 데이터에서 다음 요소를 분리해 분석하는 구조를 제공합니다.

1. **음높이/발성 계층**: 목에서 만들어지는 피치, 강세, 고음/저음 변화, 바이브레이션 경향
2. **발음/조음 계층**: 입 모양과 발음에 해당하는 음소·발음 흐름
3. **표현/창법 계층**: 호흡, 레이드백, 어택, 비브라토, 음색 경향
4. **합성 계층**: source song의 멜로디/가사/발음 정보에 style profile을 적용하는 구조

현재 ZIP은 **완성형 상용 보컬 복제 모델이 아니라**, 안전장치가 포함된 설계·코드 스캐폴드입니다. 실제 고품질 보컬 합성을 하려면 대규모 데이터, 권리 검증, 음성합성 모델, 보컬 분리, 음소 정렬, 학습 인프라가 추가로 필요합니다.

## 빠른 시작

```bash
cd authorized_vocal_style_ai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pip install -e .
```

1. `consent.json`을 열어 권리자·보컬 당사자 동의 정보를 채웁니다.
2. `all_singers_consented`를 `true`로 바꾸기 전에는 학습 코드가 실행되지 않습니다.
3. 동의받은 WAV 파일을 `data/authorized_vocals/`에 넣습니다.
4. 매니페스트 생성:

```bash
python scripts/make_manifest.py --input data/authorized_vocals --output data/manifest.json
```

5. 스타일 프로파일 학습/추출:

```bash
python -m authorized_vocal_style_ai.train --manifest data/manifest.json --consent consent.json --output outputs/style_profile.json
```

6. 연구용 커버 데모 생성:

```bash
python -m authorized_vocal_style_ai.cover --style outputs/style_profile.json --source data/source_songs/example.wav --output outputs/demo_vocal_guide.wav
```

## 폴더 구조

```text
authorized_vocal_style_ai/
├─ README_ko.md
├─ LEGAL_SAFETY.md
├─ consent.json
├─ consent_template.md
├─ requirements.txt
├─ project_config.yaml
├─ data/
│  ├─ authorized_vocals/
│  └─ source_songs/
├─ outputs/
├─ scripts/
│  ├─ make_manifest.py
│  └─ run_demo.py
├─ src/authorized_vocal_style_ai/
│  ├─ consent.py
│  ├─ audio_features.py
│  ├─ model.py
│  ├─ train.py
│  ├─ cover.py
│  └─ watermark.py
└─ tests/
   └─ test_consent.py
```

## 중요한 제한

- “완벽한 특정 가수 모창”을 자동 생성하는 모델이 아닙니다.
- 유명 가수, 사망한 가수, 일반인, 지인의 목소리도 권리자 동의 없이 학습시키면 안 됩니다.
- 결과물에는 `watermark.py`로 생성 정보와 동의 기반 사용 표시를 남기도록 설계했습니다.
- 음원 자체의 저작권과 보컬 음성의 권리는 별개입니다. 반주·멜로디·가사 사용 권리도 확인해야 합니다.

## 다음 개발 단계

1. 보컬 분리: Demucs/Spleeter 등으로 보컬 stem 분리
2. 음소 정렬: WhisperX/MFA 등으로 가사와 음성 alignment
3. 피치 추출: CREPE, RMVPE 등 정밀 F0 추출
4. 보컬 합성: Diffusion/TTS/VC 계열 모델 연결
5. 평가: 음색 유사도, 발음 명료도, 창법 유사도, 사칭 위험도 평가
6. 배포 안전장치: 권리 검증, 워터마크, 사용 로그, 출력 고지 문구
