# migrations/ - Alembic 마이그레이션

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

비동기 SQLAlchemy 2.0 마이그레이션 관리

## 명령어

```bash
# 프로젝트 루트에서 실행
alembic current                           # 현재 상태
alembic revision --autogenerate -m "설명"  # 마이그레이션 생성
alembic upgrade head                      # 최신으로 적용
alembic downgrade -1                      # 1단계 롤백
alembic history                           # 히스토리 확인
```

## 파일 구조

```
migrations/
├── env.py              # 비동기 환경 설정
├── script.py.mako      # 마이그레이션 템플릿
├── versions/           # 마이그레이션 파일들
└── CLAUDE.md           # 이 문서
```

## 새 모델 추가 시

1. `src/serve/models/`에 모델 정의
2. `src/serve/models/__init__.py`에서 임포트
3. **`env.py`에 모델 임포트 추가** (autogenerate가 모델을 인식하기 위해 필수)
4. 마이그레이션 생성: `alembic revision --autogenerate -m "설명"`
5. 생성된 파일 검토 후 적용: `alembic upgrade head`

## 주의사항

- SQLAlchemy 예약어 피하기: `metadata`, `query` 등
- 프로덕션 배포 전 마이그레이션 파일 리뷰 필수
- SQLite → PostgreSQL 전환 시 데이터 타입 호환성 확인
