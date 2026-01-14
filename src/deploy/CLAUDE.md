# deploy/ - Hugging Face Hub 배포

모델을 Hugging Face Hub에 업로드/다운로드하는 스크립트

## 구조

```
deploy/
├── CLAUDE.md
├── 01_upload_to_hub.py      # HF Hub 업로드
└── 02_download_from_hub.py  # HF Hub 다운로드
```

## 주요 기능

| 파일 | 기능 |
|------|------|
| `01_upload_to_hub.py` | LoRA 어댑터를 HF Hub에 업로드 |
| `02_download_from_hub.py` | HF Hub에서 모델 다운로드 |

## 환경 설정

```bash
# .env 파일에 HF 토큰 설정 필요
HUGGINGFACE_TOKEN=hf_xxxxx
```

## 사용법

```bash
# 업로드
python src/deploy/01_upload_to_hub.py \
    --adapter-path models/fine-tuned/lora-mistral-custom \
    --repo-name llama3-8b-ko-chat-v1 \
    --public

# 다운로드
python src/deploy/02_download_from_hub.py \
    --repo-id username/llama3-8b-ko-chat-v1 \
    --output-dir models/downloaded
```

## 주의사항

1. **HF 토큰**: write 권한 필요
2. **라이선스**: Llama 3 Community License 준수
3. **Model Card**: 업로드 시 자동 생성됨
