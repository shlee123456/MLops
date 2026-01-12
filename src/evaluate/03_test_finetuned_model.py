#!/usr/bin/env python3
"""
Fine-tuned 모델 추론 테스트
베이스 모델 vs LoRA vs QLoRA 비교
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import time
from pathlib import Path
import json

def load_base_model(model_name="meta-llama/Meta-Llama-3-8B-Instruct"):
    """베이스 모델 로드"""
    print(f"\n{'='*80}")
    print(f"베이스 모델 로드 중: {model_name}")
    print(f"{'='*80}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    print(f"✓ 베이스 모델 로드 완료")
    return tokenizer, model

def load_finetuned_model(base_model_name, adapter_path, model_type="LoRA"):
    """Fine-tuned 모델 로드 (LoRA/QLoRA)"""
    print(f"\n{'='*80}")
    print(f"{model_type} 모델 로드 중: {adapter_path}")
    print(f"{'='*80}")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    # 베이스 모델 로드
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    # LoRA adapter 적용
    model = PeftModel.from_pretrained(
        base_model,
        adapter_path,
        torch_dtype=torch.float16,
    )

    print(f"✓ {model_type} 모델 로드 완료")
    return tokenizer, model

def generate_response(model, tokenizer, prompt, max_tokens=200):
    """모델 추론 실행"""

    # LLaMA-3 Instruct 포맷
    messages = [
        {"role": "user", "content": prompt}
    ]

    # 토크나이저로 포맷팅
    if hasattr(tokenizer, 'apply_chat_template'):
        input_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    else:
        input_text = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    # 추론 시간 측정
    start_time = time.time()

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    inference_time = time.time() - start_time

    # 응답 디코딩
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 응답 부분만 추출
    if "<|start_header_id|>assistant<|end_header_id|>" in generated_text:
        response = generated_text.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()
    else:
        response = generated_text[len(input_text):].strip()

    return response, inference_time

def test_models():
    """모델 비교 테스트"""

    base_model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
    lora_adapter_path = "models/fine-tuned/lora-mistral-custom/checkpoint-1188"
    qlora_adapter_path = "models/fine-tuned/qlora-mistral-custom/checkpoint-1188"

    # 테스트 프롬프트
    test_prompts = [
        "What is Docker and why is it useful in DevOps?",
        "Explain the difference between CI and CD in software development.",
        "How do you implement a Kubernetes deployment?",
        "What are the benefits of using machine learning in production?",
        "Describe the process of fine-tuning a large language model.",
    ]

    print("\n" + "="*80)
    print("Fine-tuned 모델 추론 테스트")
    print("="*80)

    # 결과 저장
    results = []

    # 1. 베이스 모델 테스트
    print("\n[1/3] 베이스 모델 테스트")
    tokenizer_base, model_base = load_base_model(base_model_name)

    base_results = []
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- 프롬프트 {i}/{len(test_prompts)} ---")
        print(f"Q: {prompt}")

        response, time_taken = generate_response(model_base, tokenizer_base, prompt)
        print(f"A (Base): {response[:200]}...")
        print(f"추론 시간: {time_taken:.2f}s")

        base_results.append({
            "prompt": prompt,
            "response": response,
            "time": time_taken
        })

    # 메모리 정리
    del model_base
    del tokenizer_base
    torch.cuda.empty_cache()

    # 2. LoRA 모델 테스트
    print("\n[2/3] LoRA Fine-tuned 모델 테스트")
    tokenizer_lora, model_lora = load_finetuned_model(
        base_model_name,
        lora_adapter_path,
        "LoRA"
    )

    lora_results = []
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- 프롬프트 {i}/{len(test_prompts)} ---")
        print(f"Q: {prompt}")

        response, time_taken = generate_response(model_lora, tokenizer_lora, prompt)
        print(f"A (LoRA): {response[:200]}...")
        print(f"추론 시간: {time_taken:.2f}s")

        lora_results.append({
            "prompt": prompt,
            "response": response,
            "time": time_taken
        })

    # 메모리 정리
    del model_lora
    del tokenizer_lora
    torch.cuda.empty_cache()

    # 3. QLoRA 모델 테스트
    print("\n[3/3] QLoRA Fine-tuned 모델 테스트")
    tokenizer_qlora, model_qlora = load_finetuned_model(
        base_model_name,
        qlora_adapter_path,
        "QLoRA"
    )

    qlora_results = []
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- 프롬프트 {i}/{len(test_prompts)} ---")
        print(f"Q: {prompt}")

        response, time_taken = generate_response(model_qlora, tokenizer_qlora, prompt)
        print(f"A (QLoRA): {response[:200]}...")
        print(f"추론 시간: {time_taken:.2f}s")

        qlora_results.append({
            "prompt": prompt,
            "response": response,
            "time": time_taken
        })

    # 메모리 정리
    del model_qlora
    del tokenizer_qlora
    torch.cuda.empty_cache()

    # 결과 저장
    print("\n" + "="*80)
    print("결과 저장 중...")
    print("="*80)

    output_dir = Path("results/inference_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_data = {
        "base_model": base_results,
        "lora_model": lora_results,
        "qlora_model": qlora_results,
        "summary": {
            "base_avg_time": sum(r["time"] for r in base_results) / len(base_results),
            "lora_avg_time": sum(r["time"] for r in lora_results) / len(lora_results),
            "qlora_avg_time": sum(r["time"] for r in qlora_results) / len(qlora_results),
        }
    }

    output_file = output_dir / "inference_comparison.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False)

    print(f"✓ 결과 저장 완료: {output_file}")

    # 요약 출력
    print("\n" + "="*80)
    print("추론 시간 요약")
    print("="*80)
    print(f"베이스 모델 평균: {comparison_data['summary']['base_avg_time']:.2f}s")
    print(f"LoRA 모델 평균: {comparison_data['summary']['lora_avg_time']:.2f}s")
    print(f"QLoRA 모델 평균: {comparison_data['summary']['qlora_avg_time']:.2f}s")

    print("\n" + "="*80)
    print("테스트 완료!")
    print("="*80)
    print(f"\n상세 결과는 {output_file} 파일을 확인하세요.")

if __name__ == "__main__":
    test_models()
