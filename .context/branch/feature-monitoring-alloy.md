# 브랜치: feature/monitoring-alloy

## 목표
Grafana Alloy 도입으로 모니터링 에이전트 통합 (3개 → 1개)

## 변경 내용
- **제거**: Promtail, Node Exporter, cAdvisor
- **추가**: Grafana Alloy

## 영향 파일
- `docker-compose.yml`
- `deployment/configs/alloy/config.alloy` (신규)
- `deployment/configs/prometheus/prometheus.yml`
- `CLAUDE.md`, `deployment/CLAUDE.md`

## 진행 상태
- [x] Step 0: 브랜치 컨텍스트 생성
- [x] Step 1: 백업 생성
- [x] Step 2: Alloy 설정 생성
- [x] Step 3: docker-compose.yml 수정
- [x] Step 4: Prometheus 설정 수정
- [x] Step 5: 문서 업데이트
