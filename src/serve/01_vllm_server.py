#!/usr/bin/env python3
"""
Phase 3-1: vLLM OpenAI-Compatible Server

vLLM을 사용한 고성능 추론 서버
OpenAI API와 호환되는 엔드포인트 제공
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def print_server_info(args):
    """서버 정보 출력"""
    print("\n" + "="*60)
    print("  vLLM OpenAI-Compatible Server")
    print("="*60 + "\n")

    print("Configuration:")
    print(f"  Model: {args.model}")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  GPU Memory Utilization: {args.gpu_memory_utilization}")
    print(f"  Max Model Length: {args.max_model_len}")
    print(f"  Tensor Parallel Size: {args.tensor_parallel_size}")

    if args.enable_lora:
        print(f"  LoRA Enabled: True")
        if args.lora_modules:
            print(f"  LoRA Modules: {args.lora_modules}")

    print("\nAPI Endpoints:")
    print(f"  Base URL: http://{args.host}:{args.port}")
    print(f"  Completions: http://{args.host}:{args.port}/v1/completions")
    print(f"  Chat Completions: http://{args.host}:{args.port}/v1/chat/completions")
    print(f"  Models: http://{args.host}:{args.port}/v1/models")
    print(f"  Health: http://{args.host}:{args.port}/health")

    print("\nUsage Examples:")
    print("  # Test with curl")
    print(f"  curl http://{args.host}:{args.port}/v1/models")
    print()
    print("  # Chat completion")
    print(f"""  curl http://{args.host}:{args.port}/v1/chat/completions \\
    -H "Content-Type: application/json" \\
    -d '{{
      "model": "{args.model}",
      "messages": [{{"role": "user", "content": "Hello!"}}]
    }}'""")

    print("\n" + "="*60 + "\n")


def start_vllm_server(
    model: str,
    host: str = "0.0.0.0",
    port: int = 8000,
    gpu_memory_utilization: float = 0.9,
    max_model_len: int = 4096,
    tensor_parallel_size: int = 1,
    enable_lora: bool = False,
    lora_modules: str = None,
    trust_remote_code: bool = True,
    download_dir: str = None
):
    """vLLM 서버 시작"""
    try:
        from vllm.entrypoints.openai.api_server import run_server
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.engine.async_llm_engine import AsyncLLMEngine
        import uvicorn
        import asyncio
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nPlease install vLLM:")
        print("  pip install vllm")
        return

    # vLLM 엔진 설정
    engine_args = AsyncEngineArgs(
        model=model,
        tokenizer=model,
        tensor_parallel_size=tensor_parallel_size,
        gpu_memory_utilization=gpu_memory_utilization,
        max_model_len=max_model_len,
        trust_remote_code=trust_remote_code,
        download_dir=download_dir,
        enable_lora=enable_lora,
        max_loras=1 if enable_lora else None,
        max_lora_rank=64 if enable_lora else None,
    )

    # LoRA 모듈 추가
    if enable_lora and lora_modules:
        # 형식: name=path
        # 예: custom-lora=/path/to/lora
        engine_args.lora_modules = [lora_modules]

    print("Starting vLLM server...")
    print("This may take a few minutes to load the model...")

    # 서버 실행 명령어 생성 (사용자가 직접 실행할 수 있도록)
    cmd = f"""python -m vllm.entrypoints.openai.api_server \\
    --model {model} \\
    --host {host} \\
    --port {port} \\
    --gpu-memory-utilization {gpu_memory_utilization} \\
    --max-model-len {max_model_len} \\
    --tensor-parallel-size {tensor_parallel_size} \\
    --trust-remote-code"""

    if enable_lora:
        cmd += " \\\n    --enable-lora"
        if lora_modules:
            cmd += f" \\\n    --lora-modules {lora_modules}"

    if download_dir:
        cmd += f" \\\n    --download-dir {download_dir}"

    print("\nAlternatively, run manually:")
    print(cmd)
    print()

    # 실제 서버 시작
    import subprocess

    cmd_list = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", model,
        "--host", host,
        "--port", str(port),
        "--gpu-memory-utilization", str(gpu_memory_utilization),
        "--max-model-len", str(max_model_len),
        "--tensor-parallel-size", str(tensor_parallel_size),
        "--trust-remote-code"
    ]

    if enable_lora:
        cmd_list.append("--enable-lora")
        if lora_modules:
            cmd_list.extend(["--lora-modules", lora_modules])

    if download_dir:
        cmd_list.extend(["--download-dir", download_dir])

    try:
        subprocess.run(cmd_list)
    except KeyboardInterrupt:
        print("\n\nShutting down vLLM server...")
        print("✓ Server stopped")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="vLLM OpenAI-Compatible Server")

    # 기본 설정
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("BASE_MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct"),
        help="HuggingFace model name or path to fine-tuned model"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port"
    )

    # GPU 설정
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.9,
        help="GPU memory utilization (0.0-1.0)"
    )
    parser.add_argument(
        "--max-model-len",
        type=int,
        default=4096,
        help="Maximum sequence length"
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=int,
        default=1,
        help="Number of GPUs for tensor parallelism"
    )

    # LoRA 설정
    parser.add_argument(
        "--enable-lora",
        action="store_true",
        help="Enable LoRA adapters"
    )
    parser.add_argument(
        "--lora-modules",
        type=str,
        default=None,
        help="LoRA modules in format: name=path (e.g., custom-lora=./models/fine-tuned/lora-model)"
    )

    # 기타
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        default=True,
        help="Trust remote code from HuggingFace"
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default=os.getenv("HF_HOME", "./models/base"),
        help="Model download directory"
    )

    args = parser.parse_args()

    # 서버 정보 출력
    print_server_info(args)

    # 서버 시작
    start_vllm_server(
        model=args.model,
        host=args.host,
        port=args.port,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        tensor_parallel_size=args.tensor_parallel_size,
        enable_lora=args.enable_lora,
        lora_modules=args.lora_modules,
        trust_remote_code=args.trust_remote_code,
        download_dir=args.download_dir
    )


if __name__ == "__main__":
    main()
