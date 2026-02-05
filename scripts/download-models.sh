#!/bin/bash
# HuggingFace 모델 다운로드 스크립트
# Usage: ./scripts/download-models.sh [preset|model_id] [options]

set -e  # 에러 발생 시 즉시 종료

# 색상 코드
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 환경변수 체크
check_env() {
  if [ -z "$HUGGINGFACE_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  HUGGINGFACE_TOKEN 환경변수가 설정되지 않았습니다.${NC}"
    echo -e "   Gated 모델 다운로드 시 필요할 수 있습니다."
    echo -e "   .env 파일에 토큰을 설정하거나 다음과 같이 실행하세요:"
    echo -e "   ${GREEN}export HUGGINGFACE_TOKEN=hf_xxx${NC}"
    echo ""
  else
    echo -e "${GREEN}✓ HUGGINGFACE_TOKEN 설정됨${NC}"
  fi
}

# 도움말
show_help() {
  cat << EOF
HuggingFace 모델 다운로드 스크립트

사용법:
  ./scripts/download-models.sh [preset|model_id] [options]

프리셋:
  ko-chat       2shlee/llama3-8b-ko-chat-v1 (Korean LLaMA-3)
  llama31-8b    meta-llama/Llama-3.1-8B-Instruct
  mistral-7b    mistralai/Mistral-7B-Instruct-v0.2
  all           models/model_list.yaml 파일의 모든 모델

직접 다운로드:
  ./scripts/download-models.sh meta-llama/Llama-3.1-8B-Instruct

옵션:
  --local-dir PATH    다운로드 경로 지정 (기본: models/downloaded)
  --force             기존 파일 무시하고 재다운로드
  --list              다운로드된 모델 목록 확인
  --info MODEL_ID     모델 정보 조회
  -h, --help          도움말 출력

예시:
  # 프리셋으로 다운로드
  ./scripts/download-models.sh ko-chat

  # 직접 모델 ID 지정
  ./scripts/download-models.sh meta-llama/Llama-3.1-8B-Instruct

  # 특정 경로에 다운로드
  ./scripts/download-models.sh ko-chat --local-dir models/base

  # 다운로드된 모델 목록 확인
  ./scripts/download-models.sh --list

  # 모델 정보 조회
  ./scripts/download-models.sh --info meta-llama/Llama-3.1-8B-Instruct

환경변수:
  HUGGINGFACE_TOKEN    HuggingFace 토큰 (Gated 모델용)
  MODEL_CACHE_DIR      기본 다운로드 경로 (기본: models/downloaded)

EOF
}

# 다운로드 실행
download_model() {
  local model_id="$1"
  shift  # 첫 번째 인자 제거
  
  echo -e "\n${GREEN}=== HuggingFace 모델 다운로드 ===${NC}"
  echo -e "모델: ${YELLOW}$model_id${NC}\n"
  
  # .env 파일 로드 (있으면)
  if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
  fi
  
  check_env
  
  # Python 스크립트 실행
  python -m src.utils.download_model "$model_id" "$@"
  
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ 다운로드 완료${NC}"
  else
    echo -e "\n${RED}✗ 다운로드 실패${NC}"
    exit 1
  fi
}

# 메인 로직
main() {
  # 인자가 없으면 도움말 출력
  if [ $# -eq 0 ]; then
    show_help
    exit 0
  fi
  
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    
    --list)
      python -m src.utils.download_model --list
      exit 0
      ;;
    
    --info)
      if [ -z "$2" ]; then
        echo -e "${RED}✗ 모델 ID를 지정하세요${NC}"
        echo "   사용법: $0 --info meta-llama/Llama-3.1-8B-Instruct"
        exit 1
      fi
      python -m src.utils.download_model --info "$2"
      exit 0
      ;;
    
    # 프리셋
    ko-chat)
      download_model "2shlee/llama3-8b-ko-chat-v1" "${@:2}"
      ;;
    
    llama31-8b)
      download_model "meta-llama/Llama-3.1-8B-Instruct" "${@:2}"
      ;;
    
    mistral-7b)
      download_model "mistralai/Mistral-7B-Instruct-v0.2" "${@:2}"
      ;;
    
    all)
      echo -e "\n${GREEN}=== 일괄 다운로드 (model_list.yaml) ===${NC}\n"
      
      if [ ! -f models/model_list.yaml ]; then
        echo -e "${RED}✗ models/model_list.yaml 파일을 찾을 수 없습니다${NC}"
        echo "   다음 형식으로 파일을 생성하세요:"
        echo ""
        cat << 'YAML'
models:
  - id: 2shlee/llama3-8b-ko-chat-v1
    revision: main
  - id: meta-llama/Llama-3.1-8B-Instruct
    revision: main
YAML
        exit 1
      fi
      
      python -m src.utils.download_model --config models/model_list.yaml "${@:2}"
      ;;
    
    # 직접 모델 ID 지정 (슬래시 포함 여부로 판단)
    */*)
      download_model "$@"
      ;;
    
    *)
      echo -e "${RED}✗ 알 수 없는 프리셋: $1${NC}"
      echo ""
      show_help
      exit 1
      ;;
  esac
}

main "$@"
