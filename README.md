# 모창 AI 앱 프로토타입 — 동의 기반 보컬 스타일 변환 UI/백엔드 골격

이 프로젝트는 사용자가 설명한 세 화면 구조를 구현한 **로컬 프로토타입**입니다.

- 왼쪽 메뉴: `학습란`, `보컬변환란`, `반주변환란`
- 학습란: 최대 10개 보컬 파일 업로드, 총 5GB 제한 UI/서버 검증, 학습 시작 버튼, 학습 완료 후 `학습 결과 미리보기` 버튼 표시
- 미리보기: 포함된 `samples/nabiya.wav`를 사용해 1000 / 10000 / 50000 / 초정밀 단계별 비교 음원 생성
- 보컬변환란: 보컬 파일 1개 업로드, 1GB 제한, 체크포인트별 결과 생성 및 다운로드
- 반주변환란: 반주 파일 업로드, 변형 결과 생성, 보컬 결과에 맞추기용 자리 포함
- 출력: 48kHz, 16-bit PCM WAV로 저장해 “8비트처럼 들림” 문제를 피하도록 설계

## 중요한 제한

이 코드는 실제 RVC, Diffusion VC, Singing Voice Conversion 모델을 포함하지 않습니다.  
실제 특정인의 목소리·감정·뉘앙스를 완벽히 복제하는 기능은 법적·윤리적 문제가 있어, 본 골격은 **본인 또는 명시적 동의를 받은 보컬 데이터**로만 사용할 수 있는 연구/시제품 구조입니다.

현재 오디오 처리는 다음을 구현합니다.

- 음량 정규화
- RMS 기반 구간 분석
- 피치/스펙트럼/템포 기초 특징 추출
- 체크포인트별 미세한 시간축 변조 및 질감 변화 데모
- WAV 고품질 출력

실서비스 수준으로 만들려면 별도의 동의 검증, 데이터셋 정제, 화자 권리 관리, 모델 학습 서버, GPU 큐, 워터마킹/감지 로그, 악용 방지 장치가 필요합니다.

## 실행 방법

```bash
cd mochang_ai_prototype
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

브라우저에서 접속:

```text
http://127.0.0.1:8000
```

## 폴더 구조

```text
mochang_ai_prototype/
  app/
    main.py
    audio_engine.py
  static/
    index.html
    styles.css
    app.js
  samples/
    nabiya.wav
  data/
  requirements.txt
  README.md
```
