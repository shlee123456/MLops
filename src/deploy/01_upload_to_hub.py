#!/usr/bin/env python3
"""
Hugging Face Hub 모델 업로드

LoRA 어댑터를 Hugging Face Hub에 업로드합니다.
Model Card가 자동으로 생성됩니다.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def create_model_card(
    repo_name: str,
    base_model: str,
    adapter_path: str,
    language: str = "ko",
    license_type: str = "llama3",
    tags: list = None,
    training_info: dict = None
) -> str:
    """Model Card (README.md) 생성"""
    
    if tags is None:
        tags = ["korean", "llama3", "chatbot", "lora", "peft", "conversational"]
    
    # YAML frontmatter
    tags_yaml = "\n".join([f"  - {tag}" for tag in tags])
    
    # 학습 정보
    if training_info:
        training_section = f"""
## Training Details

| Parameter | Value |
|-----------|-------|
| Base Model | `{base_model}` |
| Fine-tuning | LoRA (PEFT) |
| Epochs | {training_info.get('epochs', 'N/A')} |
| Batch Size | {training_info.get('batch_size', 'N/A')} |
| Learning Rate | {training_info.get('learning_rate', 'N/A')} |
| LoRA Rank | {training_info.get('lora_r', 16)} |
| LoRA Alpha | {training_info.get('lora_alpha', 32)} |
| Target Modules | q_proj, k_proj, v_proj, o_proj |
"""
    else:
        training_section = f"""
## Training Details

- **Base Model**: `{base_model}`
- **Fine-tuning Method**: LoRA (PEFT)
- **Target Modules**: q_proj, k_proj, v_proj, o_proj
"""
    
    model_card = f"""---
language:
  - {language}
license: {license_type}
library_name: peft
base_model: {base_model}
tags:
{tags_yaml}
pipeline_tag: text-generation
---

# {repo_name}

한국어 대화를 위해 파인튜닝된 LLaMA 3 8B 모델입니다.

## Model Description

이 모델은 Meta의 LLaMA 3 8B Instruct 모델을 기반으로 한국어 챗봇 용도로 LoRA 파인튜닝되었습니다.

- **Base Model**: [{base_model}](https://huggingface.co/{base_model})
- **Language**: Korean (한국어)
- **Task**: Conversational AI / Chatbot
- **Fine-tuning**: LoRA (Parameter-Efficient Fine-Tuning)
{training_section}
## How to Use

### With PEFT (Recommended)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch

# 베이스 모델 로드
base_model = "{base_model}"
tokenizer = AutoTokenizer.from_pretrained(base_model)
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.float16,
    device_map="auto"
)

# LoRA 어댑터 적용
model = PeftModel.from_pretrained(model, "{repo_name}")

# 추론
messages = [{{"role": "user", "content": "안녕하세요!"}}]
input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.7)
    
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

### With vLLM (Production)

```bash
python -m vllm.entrypoints.openai.api_server \\
    --model {base_model} \\
    --enable-lora \\
    --lora-modules ko-chat={repo_name}
```

## Intended Uses

- 한국어 대화형 AI 서비스
- 챗봇 어시스턴트
- Q&A 시스템
- 텍스트 생성

## Limitations

- 베이스 모델(LLaMA 3)의 일반적인 한계점 적용
- 학습 데이터에 없는 도메인에서는 성능이 저하될 수 있음
- 실시간 정보나 최신 지식이 필요한 질문에는 부적합

## License

이 모델은 [Llama 3 Community License](https://llama.meta.com/llama3/license/)를 따릅니다.

## Acknowledgements

Built with Meta Llama 3

## Citation

```bibtex
@misc{{{repo_name.replace('-', '_').replace('/', '_')}}},
  author = {{shlee}},
  title = {{{repo_name}}},
  year = {{2026}},
  publisher = {{Hugging Face}},
  howpublished = {{\\url{{https://huggingface.co/{repo_name}}}}}
}}
```
"""
    return model_card


def upload_to_hub(
    adapter_path: str,
    repo_name: str,
    username: str = None,
    private: bool = False,
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    training_info: dict = None
):
    """LoRA 어댑터를 Hugging Face Hub에 업로드"""
    
    try:
        from huggingface_hub import HfApi, create_repo, upload_folder
        from peft import PeftModel, PeftConfig
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nPlease install required packages:")
        print("  pip install huggingface-hub peft")
        return False
    
    # HF 토큰 확인
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        print("✗ Error: HUGGINGFACE_TOKEN not found in environment")
        print("  Set it in .env file or export HUGGINGFACE_TOKEN=hf_xxxxx")
        return False
    
    # 어댑터 경로 확인
    adapter_path = Path(adapter_path)
    if not adapter_path.exists():
        print(f"✗ Error: Adapter path not found: {adapter_path}")
        return False
    
    # adapter_config.json 확인
    config_file = adapter_path / "adapter_config.json"
    if not config_file.exists():
        print(f"✗ Error: adapter_config.json not found in {adapter_path}")
        print("  Make sure this is a valid PEFT adapter directory")
        return False
    
    print(f"\n{'='*60}")
    print("  Hugging Face Hub Upload")
    print(f"{'='*60}\n")
    
    # API 초기화
    api = HfApi(token=hf_token)
    
    # 사용자명 확인
    if username is None:
        user_info = api.whoami()
        username = user_info["name"]
    
    # 전체 repo ID
    repo_id = f"{username}/{repo_name}"
    
    print(f"Configuration:")
    print(f"  Adapter Path: {adapter_path}")
    print(f"  Repository: {repo_id}")
    print(f"  Visibility: {'Private' if private else 'Public'}")
    print(f"  Base Model: {base_model}")
    print()
    
    # 1. 레포지토리 생성
    print("Creating repository...")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="model",
            private=private,
            token=hf_token,
            exist_ok=True  # 이미 존재하면 무시
        )
        print(f"✓ Repository created: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"⚠ Repository creation warning: {e}")
    
    # 2. Model Card 생성
    print("\nGenerating Model Card...")
    model_card = create_model_card(
        repo_name=repo_id,
        base_model=base_model,
        adapter_path=str(adapter_path),
        training_info=training_info
    )
    
    # README.md 저장
    readme_path = adapter_path / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(model_card)
    print(f"✓ Model Card saved: {readme_path}")
    
    # 3. 업로드
    print("\nUploading to Hugging Face Hub...")
    print("  This may take a few minutes...")
    
    try:
        upload_folder(
            folder_path=str(adapter_path),
            repo_id=repo_id,
            repo_type="model",
            token=hf_token,
            commit_message=f"Upload LoRA adapter - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        print(f"\n✓ Upload completed successfully!")
        print(f"\n{'='*60}")
        print(f"  Model URL: https://huggingface.co/{repo_id}")
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="Upload LoRA adapter to Hugging Face Hub"
    )
    
    parser.add_argument(
        "--adapter-path",
        type=str,
        default="models/fine-tuned/lora-mistral-custom",
        help="Path to LoRA adapter directory"
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        default="llama3-8b-ko-chat-v1",
        help="Repository name on Hugging Face Hub"
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Hugging Face username (auto-detected if not provided)"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        help="Base model name"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make repository private"
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Make repository public (default)"
    )
    
    # 학습 정보 (선택)
    parser.add_argument("--epochs", type=int, default=None, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=None, help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha")
    
    args = parser.parse_args()
    
    # 학습 정보 구성
    training_info = None
    if any([args.epochs, args.batch_size, args.learning_rate]):
        training_info = {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "lora_r": args.lora_r,
            "lora_alpha": args.lora_alpha
        }
    
    # Private 플래그 처리 (--public이 명시되면 private=False)
    is_private = args.private and not args.public
    
    # 업로드 실행
    success = upload_to_hub(
        adapter_path=args.adapter_path,
        repo_name=args.repo_name,
        username=args.username,
        private=is_private,
        base_model=args.base_model,
        training_info=training_info
    )
    
    if success:
        print("Next steps:")
        print("  1. Check your model page on Hugging Face")
        print("  2. Test loading with: python src/deploy/02_download_from_hub.py")
        print("  3. Share the model URL with others!")
    else:
        print("\nTroubleshooting:")
        print("  1. Check your HUGGINGFACE_TOKEN has write permissions")
        print("  2. Verify the adapter path exists and contains adapter_config.json")
        print("  3. Ensure you have internet connectivity")


if __name__ == "__main__":
    main()
