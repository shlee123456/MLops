#!/bin/bash
# Grafana 대시보드 테스트용 트래픽 생성 스크립트
# Usage: ./scripts/test-dashboards.sh [count]

BASE_URL="http://localhost:8080"
COUNT=${1:-5}

echo "=== Grafana 대시보드 테스트 트래픽 생성 ==="
echo "반복 횟수: $COUNT"
echo ""

# 정상 요청 (200)
echo "--- 정상 요청 (info 로그 생성) ---"
for i in $(seq 1 $COUNT); do
  curl -s "$BASE_URL/health" > /dev/null
  curl -s "$BASE_URL/" > /dev/null
  curl -s "$BASE_URL/v1/models" > /dev/null
  curl -s "$BASE_URL/v1/conversations" > /dev/null
  curl -s "$BASE_URL/v1/llm-configs" > /dev/null
  echo "  [$i/$COUNT] 정상 요청 전송"
done

# 404 에러 (존재하지 않는 경로)
echo ""
echo "--- 404 에러 생성 ---"
for i in $(seq 1 $COUNT); do
  curl -s "$BASE_URL/v1/conversations/nonexistent-id" > /dev/null
  curl -s "$BASE_URL/v1/llm-configs/99999" > /dev/null
  curl -s "$BASE_URL/not-found-path" > /dev/null
  echo "  [$i/$COUNT] 404 요청 전송"
done

# 422 에러 (잘못된 요청 바디)
echo ""
echo "--- 422 Validation 에러 생성 ---"
for i in $(seq 1 $COUNT); do
  curl -s -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "body"}' > /dev/null
  curl -s -X POST "$BASE_URL/v1/llm-configs" \
    -H "Content-Type: application/json" \
    -d '{}' > /dev/null
  echo "  [$i/$COUNT] 422 요청 전송"
done

# 500 에러 유도 (vLLM 미연결 상태에서 chat 요청)
echo ""
echo "--- 500 에러 생성 (vLLM 미연결) ---"
for i in $(seq 1 $COUNT); do
  curl -s -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "test"}], "model": "test-model"}' > /dev/null
  echo "  [$i/$COUNT] 500 요청 전송"
done

echo ""
echo "=== 완료 ==="
echo ""
echo "확인할 대시보드:"
echo "  - All Application Logs: http://localhost:3000/d/logs-dashboard"
echo "  - Error Logs 패널: level=error 로그 확인"
echo "  - FastAPI Logs 패널: path 필터 테스트"
echo "  - Log Level Distribution: info/warning/error 분포"
echo ""
echo "Loki 직접 확인:"
echo "  curl -s -G 'http://localhost:3100/loki/api/v1/query_range' \\"
echo "    --data-urlencode 'query={job=\"fastapi\"}' \\"
echo "    --data-urlencode \"start=\$(date -v-1H +%s)\" \\"
echo "    --data-urlencode \"end=\$(date +%s)\" \\"
echo "    --data-urlencode 'limit=10' | python3 -m json.tool"
