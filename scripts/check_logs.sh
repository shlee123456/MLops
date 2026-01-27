#!/bin/bash
#
# Log Verification Script
# 각 서비스의 로그 파일 생성 여부를 검증합니다.
#
# Usage: ./scripts/check_logs.sh

set -e

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "   로그 생성 검증 스크립트"
echo "=================================="
echo ""

# 프로젝트 루트 디렉토리 확인
if [ ! -d "logs" ]; then
    echo -e "${RED}❌ logs/ 디렉토리를 찾을 수 없습니다. 프로젝트 루트에서 실행하세요.${NC}"
    exit 1
fi

# 검증할 서비스 목록
declare -A services=(
    ["vllm"]="logs/vllm/*.log"
    ["fastapi"]="logs/fastapi/app.log"
    ["mlflow"]="logs/mlflow/*.log"
    ["training"]="logs/training/*.log"
    ["system"]="logs/system/*.log"
    ["inference"]="logs/inference/*.log"
)

# 서비스별 설명
declare -A descriptions=(
    ["vllm"]="vLLM 추론 서비스"
    ["fastapi"]="FastAPI 서비스"
    ["mlflow"]="MLflow 실험 추적"
    ["training"]="학습 스크립트"
    ["system"]="시스템/GPU 모니터링"
    ["inference"]="추론 메트릭"
)

# 결과 저장
total=0
found=0
missing=0

echo "서비스별 로그 파일 검증:"
echo ""

for service in "${!services[@]}"; do
    pattern="${services[$service]}"
    desc="${descriptions[$service]}"
    total=$((total + 1))

    # 로그 파일 검색
    files=($(ls $pattern 2>/dev/null || true))

    if [ ${#files[@]} -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} $desc ($service)"
        echo "    경로: $pattern"
        echo "    파일 수: ${#files[@]}"

        # 가장 최근 파일 정보
        latest=$(ls -t $pattern 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            size=$(du -h "$latest" | cut -f1)
            modified=$(stat -c %y "$latest" 2>/dev/null | cut -d'.' -f1 || stat -f "%Sm" "$latest")
            echo "    최근 파일: $(basename "$latest") ($size)"
            echo "    수정 시간: $modified"
        fi
        found=$((found + 1))
    else
        echo -e "  ${RED}✗${NC} $desc ($service)"
        echo "    경로: $pattern"
        echo -e "    ${YELLOW}로그 파일이 없습니다.${NC}"
        missing=$((missing + 1))
    fi
    echo ""
done

# 요약
echo "=================================="
echo "결과 요약:"
echo "  전체: $total"
echo -e "  생성됨: ${GREEN}$found${NC}"
echo -e "  없음: ${RED}$missing${NC}"
echo "=================================="
echo ""

# 서비스가 실행 중인지 확인 (Docker Compose)
echo "Docker 서비스 상태 확인:"
echo ""

if command -v docker &> /dev/null; then
    # vLLM
    if docker ps --format '{{.Names}}' | grep -q vllm; then
        echo -e "  ${GREEN}✓${NC} vLLM 컨테이너 실행 중"
    else
        echo -e "  ${YELLOW}⚠${NC} vLLM 컨테이너가 실행되지 않음"
    fi

    # FastAPI
    if docker ps --format '{{.Names}}' | grep -q fastapi; then
        echo -e "  ${GREEN}✓${NC} FastAPI 컨테이너 실행 중"
    else
        echo -e "  ${YELLOW}⚠${NC} FastAPI 컨테이너가 실행되지 않음"
    fi

    # MLflow
    if docker ps --format '{{.Names}}' | grep -q mlflow; then
        echo -e "  ${GREEN}✓${NC} MLflow 컨테이너 실행 중"
    else
        echo -e "  ${YELLOW}⚠${NC} MLflow 컨테이너가 실행되지 않음"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Docker가 설치되지 않았습니다."
fi

echo ""
echo "=================================="
echo ""

# 권장 사항
if [ $missing -gt 0 ]; then
    echo "📋 로그 생성 방법:"
    echo ""

    if [ ! -f "logs/vllm/"*.log ] 2>/dev/null; then
        echo "  • vLLM: docker compose -f docker/docker-compose.serving.yml up -d"
    fi

    if [ ! -f "logs/fastapi/app.log" ]; then
        echo "  • FastAPI: docker compose -f docker/docker-compose.serving.yml up -d"
        echo "    (환경변수 LOG_DIR=/logs 필요)"
    fi

    if [ ! -f "logs/mlflow/"*.log ] 2>/dev/null; then
        echo "  • MLflow: docker compose -f docker/docker-compose.mlflow.yml up -d"
    fi

    if [ ! -f "logs/training/"*.log ] 2>/dev/null; then
        echo "  • Training: python src/train/01_lora_finetune.py"
    fi

    if [ ! -f "logs/system/"*.log ] 2>/dev/null; then
        echo "  • System: python src/train/train_with_logging_example.py"
    fi

    if [ ! -f "logs/inference/"*.log ] 2>/dev/null; then
        echo "  • Inference: 현재 미사용 (InferenceLogger 통합 필요)"
    fi

    echo ""
fi

echo "📚 자세한 정보: docs/references/LOGGING.md"
echo ""

# 종료 코드
if [ $missing -eq $total ]; then
    # 모든 로그가 없으면 에러
    exit 1
else
    # 일부라도 있으면 성공
    exit 0
fi
