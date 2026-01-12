#!/usr/bin/env python3
"""
LoRA vs QLoRA 학습 결과 비교 및 시각화
"""

import json
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_trainer_state(model_path):
    """trainer_state.json 로드"""
    state_file = Path(model_path) / "checkpoint-1188" / "trainer_state.json"

    if not state_file.exists():
        print(f"파일 없음: {state_file}")
        return None

    with open(state_file, 'r') as f:
        return json.load(f)

def analyze_and_compare():
    """LoRA vs QLoRA 학습 결과 비교"""

    # 모델 경로
    lora_path = Path("models/fine-tuned/lora-mistral-custom")
    qlora_path = Path("models/fine-tuned/qlora-mistral-custom")

    # 학습 상태 로드
    lora_state = load_trainer_state(lora_path)
    qlora_state = load_trainer_state(qlora_path)

    if not lora_state or not qlora_state:
        print("학습 결과 파일을 찾을 수 없습니다.")
        return

    print("=" * 80)
    print("LoRA vs QLoRA 학습 결과 비교")
    print("=" * 80)

    # 기본 정보
    print(f"\n{'Metric':<30} {'LoRA':<20} {'QLoRA':<20}")
    print("-" * 70)
    print(f"{'Epoch':<30} {lora_state['epoch']:<20.2f} {qlora_state['epoch']:<20.2f}")
    print(f"{'Global Steps':<30} {lora_state['global_step']:<20} {qlora_state['global_step']:<20}")
    print(f"{'Batch Size':<30} {lora_state['train_batch_size']:<20} {qlora_state['train_batch_size']:<20}")

    # Loss 히스토리 추출
    lora_history = lora_state['log_history']
    qlora_history = qlora_state['log_history']

    # Loss 데이터 추출
    lora_losses = [(h['step'], h['loss']) for h in lora_history if 'loss' in h]
    qlora_losses = [(h['step'], h['loss']) for h in qlora_history if 'loss' in h]

    # 최종 Loss
    lora_final_loss = lora_losses[-1][1] if lora_losses else 0
    qlora_final_loss = qlora_losses[-1][1] if qlora_losses else 0

    print(f"{'Final Loss':<30} {lora_final_loss:<20.4f} {qlora_final_loss:<20.4f}")

    # 평균 Loss (후반부만)
    lora_avg_loss = np.mean([l[1] for l in lora_losses[-50:]])
    qlora_avg_loss = np.mean([l[1] for l in qlora_losses[-50:]])

    print(f"{'Avg Loss (last 50)':<30} {lora_avg_loss:<20.4f} {qlora_avg_loss:<20.4f}")

    # Gradient Norm 비교
    lora_grad_norms = [h['grad_norm'] for h in lora_history if 'grad_norm' in h]
    qlora_grad_norms = [h['grad_norm'] for h in qlora_history if 'grad_norm' in h]

    lora_avg_grad = np.mean(lora_grad_norms)
    qlora_avg_grad = np.mean(qlora_grad_norms)

    print(f"{'Avg Gradient Norm':<30} {lora_avg_grad:<20.4f} {qlora_avg_grad:<20.4f}")

    print("\n" + "=" * 80)
    print("시각화 생성 중...")
    print("=" * 80)

    # 결과 디렉토리 생성
    output_dir = Path("results/model_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Loss Curve 비교
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    lora_steps, lora_loss_values = zip(*lora_losses)
    qlora_steps, qlora_loss_values = zip(*qlora_losses)

    plt.plot(lora_steps, lora_loss_values, label='LoRA', alpha=0.7, linewidth=2)
    plt.plot(qlora_steps, qlora_loss_values, label='QLoRA', alpha=0.7, linewidth=2)
    plt.xlabel('Training Steps', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.title('Training Loss Comparison', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    # 2. Loss 분포 비교 (Histogram)
    plt.subplot(1, 2, 2)
    plt.hist(lora_loss_values, bins=30, alpha=0.6, label='LoRA', color='blue')
    plt.hist(qlora_loss_values, bins=30, alpha=0.6, label='QLoRA', color='orange')
    plt.xlabel('Loss Value', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Loss Distribution', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    loss_plot_path = output_dir / "loss_comparison.png"
    plt.savefig(loss_plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Loss 비교 그래프 저장: {loss_plot_path}")
    plt.close()

    # 3. Gradient Norm 비교
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    plt.plot(range(len(lora_grad_norms)), lora_grad_norms, label='LoRA', alpha=0.7)
    plt.plot(range(len(qlora_grad_norms)), qlora_grad_norms, label='QLoRA', alpha=0.7)
    plt.xlabel('Training Steps', fontsize=12)
    plt.ylabel('Gradient Norm', fontsize=12)
    plt.title('Gradient Norm During Training', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    # 4. Learning Rate 비교
    plt.subplot(1, 2, 2)
    lora_lrs = [h['learning_rate'] for h in lora_history if 'learning_rate' in h]
    qlora_lrs = [h['learning_rate'] for h in qlora_history if 'learning_rate' in h]

    plt.plot(range(len(lora_lrs)), lora_lrs, label='LoRA', alpha=0.7)
    plt.plot(range(len(qlora_lrs)), qlora_lrs, label='QLoRA', alpha=0.7)
    plt.xlabel('Training Steps', fontsize=12)
    plt.ylabel('Learning Rate', fontsize=12)
    plt.title('Learning Rate Schedule', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    grad_plot_path = output_dir / "gradient_lr_comparison.png"
    plt.savefig(grad_plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Gradient/LR 비교 그래프 저장: {grad_plot_path}")
    plt.close()

    # 5. 통계 요약 저장
    summary = {
        "LoRA": {
            "final_loss": float(lora_final_loss),
            "avg_loss_last_50": float(lora_avg_loss),
            "avg_gradient_norm": float(lora_avg_grad),
            "total_steps": lora_state['global_step'],
            "epochs": lora_state['epoch'],
            "batch_size": lora_state['train_batch_size'],
        },
        "QLoRA": {
            "final_loss": float(qlora_final_loss),
            "avg_loss_last_50": float(qlora_avg_loss),
            "avg_gradient_norm": float(qlora_avg_grad),
            "total_steps": qlora_state['global_step'],
            "epochs": qlora_state['epoch'],
            "batch_size": qlora_state['train_batch_size'],
        },
        "comparison": {
            "loss_difference": float(qlora_final_loss - lora_final_loss),
            "loss_improvement_pct": float((lora_final_loss - qlora_final_loss) / lora_final_loss * 100) if lora_final_loss > 0 else 0,
        }
    }

    summary_path = output_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, indent=2, fp=f)
    print(f"✓ 요약 통계 저장: {summary_path}")

    print("\n" + "=" * 80)
    print("결론")
    print("=" * 80)

    if lora_final_loss < qlora_final_loss:
        winner = "LoRA"
        diff = qlora_final_loss - lora_final_loss
        print(f"✓ LoRA가 더 낮은 loss 달성 ({lora_final_loss:.4f} vs {qlora_final_loss:.4f}, 차이: {diff:.4f})")
    else:
        winner = "QLoRA"
        diff = lora_final_loss - qlora_final_loss
        print(f"✓ QLoRA가 더 낮은 loss 달성 ({qlora_final_loss:.4f} vs {lora_final_loss:.4f}, 차이: {diff:.4f})")

    print(f"\n권장사항:")
    print(f"  - 성능 우선: {winner}")
    print(f"  - 메모리 효율: QLoRA (4-bit 양자화, VRAM 절약)")
    print(f"  - 학습 속도: LoRA (Full precision, 더 빠른 연산)")

    print(f"\n다음 단계:")
    print(f"  1. Fine-tuned 모델 추론 테스트")
    print(f"  2. Gradio 데모로 품질 비교")
    print(f"  3. vLLM 서버 구축")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_and_compare()
