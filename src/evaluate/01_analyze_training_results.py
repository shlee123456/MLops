#!/usr/bin/env python3
"""
MLflow 학습 결과 분석 스크립트
LoRA vs QLoRA 실험 비교
"""

import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
from pathlib import Path
import json

def analyze_training_results():
    """MLflow 실험 결과 분석"""

    # MLflow 클라이언트 초기화
    mlflow.set_tracking_uri("file:./mlruns")
    client = MlflowClient()

    # 실험 목록 조회
    experiments = client.search_experiments()

    print("=" * 80)
    print("MLflow 학습 결과 분석")
    print("=" * 80)

    for exp in experiments:
        print(f"\n실험: {exp.name} (ID: {exp.experiment_id})")
        print("-" * 80)

        # 해당 실험의 모든 run 조회
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            order_by=["start_time DESC"]
        )

        if not runs:
            print("  실행 기록 없음\n")
            continue

        # 결과 저장용 리스트
        results = []

        for run in runs:
            run_data = {
                "run_id": run.info.run_id,
                "run_name": run.data.tags.get("mlflow.runName", "Unknown"),
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
            }

            # 파라미터 추출
            params = run.data.params
            run_data.update({
                "model_name": params.get("model_name", "N/A"),
                "method": params.get("method", "N/A"),
                "learning_rate": params.get("learning_rate", "N/A"),
                "batch_size": params.get("batch_size", "N/A"),
                "num_epochs": params.get("num_epochs", "N/A"),
                "lora_r": params.get("lora_r", "N/A"),
                "lora_alpha": params.get("lora_alpha", "N/A"),
            })

            # 메트릭 추출
            metrics = run.data.metrics
            run_data.update({
                "train_loss": metrics.get("train_loss", "N/A"),
                "eval_loss": metrics.get("eval_loss", "N/A"),
                "train_runtime": metrics.get("train_runtime", "N/A"),
                "train_samples_per_second": metrics.get("train_samples_per_second", "N/A"),
            })

            results.append(run_data)

            # 개별 실행 정보 출력
            print(f"\n  Run: {run_data['run_name']}")
            print(f"    Run ID: {run_data['run_id']}")
            print(f"    Status: {run_data['status']}")
            print(f"    Method: {run_data['method']}")
            print(f"    Model: {run_data['model_name']}")
            print(f"\n    하이퍼파라미터:")
            print(f"      Learning Rate: {run_data['learning_rate']}")
            print(f"      Batch Size: {run_data['batch_size']}")
            print(f"      Epochs: {run_data['num_epochs']}")
            print(f"      LoRA r: {run_data['lora_r']}")
            print(f"      LoRA alpha: {run_data['lora_alpha']}")
            print(f"\n    메트릭:")
            print(f"      Train Loss: {run_data['train_loss']}")
            print(f"      Eval Loss: {run_data['eval_loss']}")
            print(f"      Train Runtime: {run_data['train_runtime']}")
            print(f"      Samples/sec: {run_data['train_samples_per_second']}")
            print(f"    " + "-" * 76)

        # DataFrame으로 변환
        df = pd.DataFrame(results)

        # 결과 저장
        output_dir = Path("results/training_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)

        # CSV 저장
        csv_path = output_dir / f"experiment_{exp.experiment_id}_results.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n결과 저장: {csv_path}")

        # JSON 저장
        json_path = output_dir / f"experiment_{exp.experiment_id}_results.json"
        df.to_json(json_path, orient='records', indent=2)
        print(f"결과 저장: {json_path}")

    print("\n" + "=" * 80)
    print("비교 분석")
    print("=" * 80)

    # LoRA vs QLoRA 비교
    lora_runs = [r for r in results if r.get('method') == 'lora']
    qlora_runs = [r for r in results if r.get('method') == 'qlora']

    if lora_runs and qlora_runs:
        print("\nLoRA vs QLoRA 비교:")
        print("-" * 80)

        # 최신 실행만 비교
        latest_lora = lora_runs[0]
        latest_qlora = qlora_runs[0]

        print(f"\n{'Metric':<30} {'LoRA':<20} {'QLoRA':<20} {'차이':<15}")
        print("-" * 85)

        # 숫자 메트릭만 비교
        metric_keys = ['train_loss', 'eval_loss', 'train_runtime', 'train_samples_per_second']

        for key in metric_keys:
            lora_val = latest_lora.get(key)
            qlora_val = latest_qlora.get(key)

            try:
                lora_num = float(lora_val) if lora_val != "N/A" else None
                qlora_num = float(qlora_val) if qlora_val != "N/A" else None

                if lora_num is not None and qlora_num is not None:
                    diff = qlora_num - lora_num
                    diff_pct = (diff / lora_num * 100) if lora_num != 0 else 0
                    print(f"{key:<30} {lora_num:<20.4f} {qlora_num:<20.4f} {diff:+.4f} ({diff_pct:+.1f}%)")
                else:
                    print(f"{key:<30} {str(lora_val):<20} {str(qlora_val):<20} N/A")
            except:
                print(f"{key:<30} {str(lora_val):<20} {str(qlora_val):<20} N/A")

        print("\n" + "=" * 80)
        print("결론:")
        print("-" * 80)

        # 자동 결론 생성
        try:
            lora_loss = float(latest_lora.get('train_loss', 0))
            qlora_loss = float(latest_qlora.get('train_loss', 0))
            lora_speed = float(latest_lora.get('train_samples_per_second', 0))
            qlora_speed = float(latest_qlora.get('train_samples_per_second', 0))

            if lora_loss < qlora_loss:
                print(f"✓ LoRA가 더 낮은 Loss 달성 ({lora_loss:.4f} vs {qlora_loss:.4f})")
            else:
                print(f"✓ QLoRA가 더 낮은 Loss 달성 ({qlora_loss:.4f} vs {lora_loss:.4f})")

            if lora_speed > qlora_speed:
                print(f"✓ LoRA가 더 빠른 학습 속도 ({lora_speed:.2f} vs {qlora_speed:.2f} samples/sec)")
            else:
                print(f"✓ QLoRA가 더 빠른 학습 속도 ({qlora_speed:.2f} vs {lora_speed:.2f} samples/sec)")

            print(f"\n권장사항:")
            print(f"  - 성능 우선: {'LoRA' if lora_loss < qlora_loss else 'QLoRA'}")
            print(f"  - 속도 우선: {'LoRA' if lora_speed > qlora_speed else 'QLoRA'}")
            print(f"  - 메모리 효율: QLoRA (4-bit 양자화)")

        except Exception as e:
            print(f"자동 분석 실패: {e}")

    print("\n" + "=" * 80)
    print("MLflow UI에서 더 자세한 분석:")
    print("  mlflow ui")
    print("  http://localhost:5000")
    print("=" * 80)

if __name__ == "__main__":
    analyze_training_results()
