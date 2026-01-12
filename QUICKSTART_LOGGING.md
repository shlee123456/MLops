# 로깅 시스템 빠른 시작

5분 안에 세분화된 로깅 시스템을 시작하세요.

## 1분: 로깅 테스트

```bash
# 테스트 스크립트 실행
./test_logging.sh
```

이 스크립트는:
- 예제 학습 루프 실행
- GPU 모니터링 실행
- 로그 파일 생성 확인
- JSON 로그 샘플 출력

## 2분: Docker 서비스 시작

```bash
# 환경 변수 설정
cp .env.docker .env

# 모든 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

## 3분: Grafana에서 로그 확인

1. 브라우저에서 http://localhost:3000 열기
2. 로그인: `admin` / `admin`
3. 왼쪽 메뉴 > **Explore**
4. 데이터소스: **Loki** 선택
5. 쿼리 입력:
   ```logql
   {job="training"}
   ```
6. **Run Query** 클릭

## 4분: 대시보드 보기

1. 왼쪽 메뉴 > **Dashboards**
2. **MLOps** 폴더 선택
3. 다음 대시보드 확인:
   - **Training Metrics**: 학습 로그
   - **System Overview**: GPU/CPU 상태
   - **Unified Logs**: 통합 로그 뷰

## 5분: 실제 학습 실행

```bash
# QLoRA fine-tuning 실행 (Docker)
docker-compose run --rm --gpus all \
  -e LOG_DIR=/logs \
  -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
  training \
  python /app/src/train/02_qlora_finetune.py \
  /app/data/synthetic_train.json 1 4 2e-4 16
```

또는 로컬에서:

```bash
source venv/bin/activate
python src/train/02_qlora_finetune.py
```

## 실시간 모니터링

학습 중 다음을 확인할 수 있습니다:

### Grafana (http://localhost:3000)
- **Training Metrics** 대시보드
  - 실시간 Loss 추이
  - Epoch/Step 진행 상황
  - 학습률 변화

- **System Overview** 대시보드
  - GPU 메모리 사용률
  - GPU 온도 및 전력
  - CPU/메모리 상태

### MLflow (http://localhost:5000)
- 실험 파라미터
- 메트릭 비교
- 모델 아티팩트

### 로그 파일
```bash
# 실시간 로그 스트림
tail -f logs/training/*.log | jq .

# Loss 값만
tail -f logs/training/*.log | jq '.loss'
```

## 주요 로그 쿼리

### Grafana Loki에서 사용:

```logql
# 모든 학습 로그
{job="training"}

# 특정 Epoch
{job="training"} | json | epoch="1"

# Loss < 0.1인 경우
{job="training"} | json | loss < 0.1

# 에러만
{level="ERROR"}

# GPU 메모리 사용률
{job="system"} | json | line_format "GPU {{.gpu_id}}: {{.gpu_memory_percent}}%"

# 평균 Loss (5분)
avg_over_time({job="training"} | json | unwrap loss [5m])
```

## 다음 단계

1. **커스텀 대시보드 만들기**
   - Grafana > Create > Dashboard
   - Panel 추가 및 쿼리 작성

2. **알림 설정**
   - Grafana > Alerting > Alert Rules
   - GPU 메모리 > 90% 시 알림 등

3. **자신의 코드에 로깅 통합**
   - [로깅 통합 가이드](LOGGING_INTEGRATION_GUIDE.md) 참고

## 트러블슈팅

### Docker 서비스가 시작되지 않음
```bash
docker-compose logs [service-name]
docker-compose restart [service-name]
```

### Grafana에 로그가 보이지 않음
```bash
# Loki 상태 확인
curl http://localhost:3100/ready

# Promtail 로그 확인
docker-compose logs promtail

# 로그 파일 권한 확인
ls -la logs/
```

### GPU가 인식되지 않음
```bash
# NVIDIA Docker 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## 참고 문서

- [상세 로깅 가이드](LOGGING_GUIDE.md)
- [로깅 통합 가이드](LOGGING_INTEGRATION_GUIDE.md)
- [Docker 빠른 시작](DOCKER_QUICKSTART.md)
- [배포 가이드](deployment/README.md)
