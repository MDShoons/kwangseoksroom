# 배포 가이드

## 로컬 테스트

```bash
pip install -r requirements.txt
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

접속 주소:

```text
http://localhost:8000
```

## GitHub Pages와의 차이

GitHub Pages는 HTML/CSS/JS만 실행할 수 있는 정적 호스팅입니다. 이 프로젝트는 FastAPI와 Python 처리가 필요하므로 GitHub Pages에 단독 배포하면 AI 처리 기능이 작동하지 않습니다.

가능한 배포 방식:

1. Render, Railway, Fly.io, AWS, GCP, Azure 같은 서버에 FastAPI 배포
2. 기존 GitHub Pages 사이트에서는 해당 서버 주소로 링크 연결
3. 추후 GPU 처리가 필요하면 별도 GPU 서버를 API로 연결

## 기존 사이트 메뉴 예시

```html
<li><a href="https://your-ai-server.example.com/" target="_blank">AI 보컬 연구실</a></li>
```

## 회원 전용 연결 방식

기존 사이트가 자체 로그인 기능을 가진 경우, 다음 방식 중 하나를 선택합니다.

- 기존 사이트에서 로그인 회원에게만 AI 서버 링크 노출
- AI 서버에 별도 로그인 기능 추가
- 기존 사이트의 세션/JWT 토큰을 AI 서버에서 검증

프로토타입에는 로그인 시스템이 포함되어 있지 않습니다.
