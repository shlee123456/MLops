# Migrations CLAUDE.md

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md)를 먼저 참조하세요.

## 목적

SQLAlchemy 모델의 데이터베이스 스키마 버전 관리

## 기술 스택

- Alembic (async 템플릿)
- SQLAlchemy 2.0+ ORM
- aiosqlite (비동기 SQLite)

## 자주 사용하는 명령어

```bash
# 현재 리비전 확인
alembic current

# 마이그레이션 히스토리
alembic history

# 새 마이그레이션 생성 (자동 감지)
alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
alembic upgrade head

# 특정 리비전으로 다운그레이드
alembic downgrade -1

# 모든 마이그레이션 롤백
alembic downgrade base
```

## 주의 사항

1. **마이그레이션 생성 전 확인**
   - 모델 변경 후 반드시 autogenerate로 마이그레이션 생성
   - 생성된 파일 검토 후 적용

2. **프로덕션 배포**
   - `alembic upgrade head` 실행 필수
   - `init_db()` 대신 Alembic 사용 권장

3. **마이그레이션 파일 관리**
   - versions/ 디렉토리의 파일은 수정하지 않음
   - 필요시 새 마이그레이션으로 수정

## 디렉토리 구조

```
migrations/
├── env.py           # Alembic 환경 설정
├── script.py.mako   # 마이그레이션 템플릿
├── versions/        # 마이그레이션 파일들
│   └── *.py
├── README           # Alembic 기본 README
└── CLAUDE.md        # 이 문서
```
