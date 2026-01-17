# src/evaluate/ - 모델 평가

> **상위 문서**: [/CLAUDE.md](../../CLAUDE.md) - 프로젝트 전체 규칙, 환경변수, 세션 히스토리/터미널 로그 기록 방법 참조

Fine-tuned 모델 성능 분석 및 비교

## 파일

| 파일 | 설명 |
|------|------|
| `01_analyze_training_results.py` | MLflow 학습 결과 분석 |
| `02_compare_models.py` | 모델 간 비교 |
| `03_test_finetuned_model.py` | Fine-tuned 모델 테스트 |

## 실행

```bash
python src/evaluate/01_analyze_training_results.py
python src/evaluate/02_compare_models.py
python src/evaluate/03_test_finetuned_model.py
```

## 결과 저장 위치

```
results/
├── inference_comparison/
│   └── inference_comparison.json
├── model_comparison/
│   ├── gradient_lr_comparison.png
│   ├── loss_comparison.png
│   └── summary.json
└── training_analysis/
    └── experiment_*_results.{csv,json}
```

## MLflow 결과 분석

```python
import mlflow

# 실험 결과 조회
experiment = mlflow.get_experiment_by_name("llm-finetuning")
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

# 메트릭 비교
best_run = runs.sort_values("metrics.eval_loss").iloc[0]
```
