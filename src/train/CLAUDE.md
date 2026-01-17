# src/train/ - 학습 파이프라인

> **상위 문서**: [/CLAUDE.md](../../CLAUDE.md) - 프로젝트 전체 규칙, 환경변수, 세션 히스토리/터미널 로그 기록 방법 참조

PEFT(LoRA/QLoRA)를 활용한 LLM Fine-tuning

## 파일

| 파일 | 설명 |
|------|------|
| `01_lora_finetune.py` | LoRA (fp16/bf16) |
| `02_qlora_finetune.py` | QLoRA (4-bit) |
| `train_with_logging_example.py` | 로깅 콜백 예제 |

## 실행

```bash
python src/train/01_lora_finetune.py   # LoRA
python src/train/02_qlora_finetune.py  # QLoRA (VRAM 절약)
```

## 핵심 설정

### LoRA Config
```python
LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.1,
    task_type=TaskType.CAUSAL_LM
)
```

### QLoRA (4-bit)
```python
BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)
```

### TrainingArguments
```python
TrainingArguments(
    output_dir="./models/fine-tuned/lora-llama3",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    num_train_epochs=3,
    fp16=True,
    gradient_checkpointing=True,  # OOM 방지
)
```

## 로깅 콜백 패턴

```python
from src.utils.logging_utils import TrainingLogger

class LoggingCallback(TrainerCallback):
    def __init__(self):
        self.logger = TrainingLogger("lora-finetune")

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            self.logger.log_step(
                epoch=state.epoch,
                step=state.global_step,
                loss=logs.get("loss", 0),
                learning_rate=logs.get("learning_rate", 0)
            )
```

## 출력 경로

- 모델: `models/fine-tuned/lora-{model}-{timestamp}/`
- MLflow: `mlruns/` (실험명: `llm-finetuning`)

## OOM 해결

1. `batch_size` 감소: 4 → 2 → 1
2. `max_length` 감소: 2048 → 1024 → 512
3. `gradient_checkpointing=True`
4. QLoRA 사용 (4-bit)
