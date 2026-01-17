# MLOps Chatbot Project

GPU 자원을 활용한 커스텀 챗봇 구축 프로젝트. LLM Fine-tuning부터 프로덕션 배포까지 전체 MLOps 파이프라인.

## 기술 스택

| 분류 | 기술 |
|------|------|
| Core ML | PyTorch, Transformers, PEFT, bitsandbytes |
| Serving | vLLM, FastAPI, Gradio |
| MLOps | MLflow, DVC |
| Database | SQLAlchemy 2.0+, Alembic, SQLite/PostgreSQL |
| Monitoring | Prometheus, Grafana, Loki, structlog |
| DevOps | Docker, Docker Compose |

## 서브 CLAUDE.md 목록

| 경로 | 설명 |
|------|------|
| [src/serve/CLAUDE.md](src/serve/CLAUDE.md) | FastAPI 서빙 (클린 아키텍처) |
| [src/train/CLAUDE.md](src/train/CLAUDE.md) | LoRA/QLoRA Fine-tuning |
| [src/data/CLAUDE.md](src/data/CLAUDE.md) | 데이터 파이프라인 |
| [src/evaluate/CLAUDE.md](src/evaluate/CLAUDE.md) | 모델 평가 |
| [src/utils/CLAUDE.md](src/utils/CLAUDE.md) | 로깅 유틸리티 |
| [deployment/CLAUDE.md](deployment/CLAUDE.md) | Docker 배포 |

---

## ⚠️ 필수 실행 규칙

### 1. 터미널 로그 기록
```bash
[명령어] 2>&1 | tee .context/terminal/[명령어]_$(date +%s).log
```

### 2. 서브 CLAUDE.md 관리
- 새 디렉토리 생성 → 서브 CLAUDE.md 생성
- 기존 구조 변경 → 관련 CLAUDE.md 업데이트

### 3. 세션 관리
- **시작**: `.context/history/`에서 최근 세션 확인
- **종료**: `.context/history/session_YYYY-MM-DD_HH-MM.md` 기록

### 4. Git 커밋 규칙
```
<type>: <한글 설명>
```
- 커밋 메시지는 **한글**로 작성
- `Co-Authored-By` 태그 **사용 금지**

---

## 자주 사용하는 명령어

### 서버 실행
```bash
# vLLM 서버 (GPU 필요)
python src/serve/01_vllm_server.py  # :8000

# FastAPI 서버
python -m src.serve.main  # :8080

# MLflow UI
mlflow ui --port 5000
```

### 테스트
```bash
python -m pytest tests/serve/ -v
```

### 마이그레이션 (Alembic)
```bash
alembic current                        # 현재 상태
alembic revision --autogenerate -m "설명"  # 생성
alembic upgrade head                   # 적용
```

### Docker
```bash
docker-compose up -d        # 전체 스택
docker-compose logs -f      # 로그
docker-compose down         # 중지
```

---

## 세션 관리 프로토콜

### 세션 시작
```
세션시작
```
→ `.context/history/` 최근 파일 확인, TODO 파악

### 세션 종료
```
세션종료
```
→ `.context/history/session_YYYY-MM-DD_HH-MM.md` 생성

---

## 환경 변수 (주요)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VLLM_BASE_URL` | http://localhost:8000/v1 | vLLM 서버 |
| `FASTAPI_PORT` | 8080 | FastAPI 포트 |
| `DATABASE_URL` | sqlite+aiosqlite:///./mlops_chat.db | DB |
| `ENABLE_AUTH` | false | 인증 활성화 |

환경 파일: `cp env.example .env`

---

## 참고 문서

- [CLAUDE.md 가이드라인](docs/guides/CLAUDE-GUIDE.md) - 문서 작성 규칙
- [로깅 가이드](docs/guides/LOGGING.md) - 구조화된 로깅
- [vLLM 가이드](docs/guides/VLLM.md) - vLLM 서빙
