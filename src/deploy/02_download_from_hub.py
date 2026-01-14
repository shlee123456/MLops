#!/usr/bin/env python3
"""
Hugging Face Hub 모델 다운로드

Hugging Face Hub에서 LoRA 어댑터를 다운로드하고 테스트합니다.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def download_from_hub(
    repo_id: str,
    output_dir: str = None,
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
):
    """Hugging Face Hub에서 LoRA 어댑터 다운로드"""
    
    try:
        from huggingface_hub import snapshot_download, hf_hub_download
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nPlease install huggingface-hub:")
        print("  pip install huggingface-hub")
        return None
    
    # HF 토큰 (private repo인 경우 필요)
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    print(f"\n{'='*60}")
    print("  Hugging Face Hub Download")
    print(f"{'='*60}\n")
    
    print(f"Repository: {repo_id}")
    
    # 출력 디렉토리 설정
    if output_dir is None:
        repo_name = repo_id.split("/")[-1]
        output_dir = f"models/downloaded/{repo_name}"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Output Directory: {output_dir}")
    print()
    
    # 다운로드
    print("Downloading from Hugging Face Hub...")
    try:
        local_path = snapshot_download(
            repo_id=repo_id,
            local_dir=str(output_path),
            token=hf_token,
            local_dir_use_symlinks=False
        )
        print(f"\n✓ Download completed: {local_path}")
        return local_path
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return None


def test_loaded_model(
    adapter_path: str,
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    test_prompt: str = "안녕하세요! 자기소개 부탁드려요."
):
    """다운로드한 모델 테스트"""
    
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import PeftModel
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nPlease install required packages:")
        print("  pip install torch transformers peft")
        return
    
    print(f"\n{'='*60}")
    print("  Testing Downloaded Model")
    print(f"{'='*60}\n")
    
    # GPU 확인
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # 토크나이저 로드
    print(f"\nLoading tokenizer from {base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        token=os.getenv("HUGGINGFACE_TOKEN")
    )
    
    # 베이스 모델 로드
    print(f"Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        token=os.getenv("HUGGINGFACE_TOKEN")
    )
    
    # LoRA 어댑터 적용
    print(f"Applying LoRA adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(model, adapter_path)
    
    print("✓ Model loaded successfully!")
    
    # 테스트 추론
    print(f"\n{'='*60}")
    print("  Test Inference")
    print(f"{'='*60}\n")
    
    print(f"Prompt: {test_prompt}\n")
    
    # LLaMA 3 chat 포맷
    messages = [{"role": "user", "content": test_prompt}]
    
    if hasattr(tokenizer, 'apply_chat_template'):
        input_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    else:
        input_text = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{test_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    
    inputs = tokenizer(input_text, return_tensors="pt")
    if device == "cuda":
        inputs = inputs.to("cuda")
    
    # 생성
    print("Generating response...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # 디코딩
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 응답 부분만 추출
    if "assistant" in response.lower():
        response = response.split("assistant")[-1].strip()
    
    print(f"Response:\n{response}")
    
    print(f"\n{'='*60}")
    print("  Test Completed!")
    print(f"{'='*60}\n")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="Download LoRA adapter from Hugging Face Hub"
    )
    
    parser.add_argument(
        "--repo-id",
        type=str,
        required=True,
        help="Hugging Face repository ID (e.g., username/model-name)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for downloaded model"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        help="Base model name"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the downloaded model after download"
    )
    parser.add_argument(
        "--test-prompt",
        type=str,
        default="안녕하세요! 자기소개 부탁드려요.",
        help="Test prompt for model testing"
    )
    
    args = parser.parse_args()
    
    # 다운로드
    local_path = download_from_hub(
        repo_id=args.repo_id,
        output_dir=args.output_dir,
        base_model=args.base_model
    )
    
    if local_path and args.test:
        test_loaded_model(
            adapter_path=local_path,
            base_model=args.base_model,
            test_prompt=args.test_prompt
        )
    elif local_path:
        print("\nNext steps:")
        print(f"  1. Test the model: python src/deploy/02_download_from_hub.py --repo-id {args.repo_id} --test")
        print("  2. Use in your application with PEFT")
        print("  3. Deploy with vLLM for production")


if __name__ == "__main__":
    main()
