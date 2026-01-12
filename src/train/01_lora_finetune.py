#!/usr/bin/env python3
"""
Phase 2-3: LoRA Fine-tuning

PEFT(Parameter-Efficient Fine-Tuning)를 사용한 효율적인 모델 학습
MLflow로 실험을 추적합니다.
"""

import os
import sys
import json
import torch
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from datasets import load_dataset, Dataset
from transformers import (
    TrainerCallback,
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
    print("⚠ MLflow not installed. Experiment tracking disabled.")
    print("  Run: pip install mlflow")

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.logging_utils import TrainingLogger, SystemLogger


def load_training_data(data_path: str):
    """학습 데이터 로드"""
    print(f"\n{'='*60}")
    print("Loading Training Data")
    print(f"{'='*60}\n")

    data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # JSON 파일 로드
    with open(data_path, "r") as f:
        if data_path.suffix == ".json":
            data = json.load(f)
        elif data_path.suffix == ".jsonl":
            data = [json.loads(line) for line in f]
        else:
            raise ValueError(f"Unsupported file format: {data_path.suffix}")

    print(f"✓ Loaded {len(data)} examples")

    # HuggingFace Dataset으로 변환
    dataset = Dataset.from_list(data)

    print(f"✓ Dataset created")
    print(f"  Features: {list(dataset.features.keys())}")
    print(f"  Number of examples: {len(dataset)}")

    return dataset


def format_instruction(example):
    """
    Instruction 형식으로 데이터 포맷팅

    Template:
    ### Instruction:
    {instruction}

    ### Input:
    {input}

    ### Response:
    {output}
    """
    instruction = example.get("instruction", "")
    input_text = example.get("input", "")
    output = example.get("output", "")

    if input_text:
        prompt = f"""### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
    else:
        prompt = f"""### Instruction:
{instruction}

### Response:
{output}"""

    return {"text": prompt}


def prepare_dataset(dataset, tokenizer, max_length=512):
    """데이터셋 전처리 및 토큰화"""
    print(f"\n{'='*60}")
    print("Preparing Dataset")
    print(f"{'='*60}\n")

    # Instruction 포맷 적용
    print("Formatting examples...")
    dataset = dataset.map(format_instruction)

    # 토큰화
    print("Tokenizing examples...")

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )

    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing"
    )

    print(f"✓ Dataset prepared")
    print(f"  Total examples: {len(tokenized_dataset)}")

    return tokenized_dataset


def setup_lora_model(model_name, lora_r=16, lora_alpha=32, lora_dropout=0.05):
    """LoRA 설정 및 모델 준비"""
    print(f"\n{'='*60}")
    print("Setting up LoRA Model")
    print(f"{'='*60}\n")

    # 디바이스 확인
    if torch.cuda.is_available():
        device = "cuda"
        print(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        print("⚠ Using CPU (training will be slow)")

    # Tokenizer 로드
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        token=os.getenv("HUGGINGFACE_TOKEN"),
        trust_remote_code=True
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

    # 모델 로드
    print("Loading base model...")
    # GPU 0만 사용하도록 설정 (메모리 관리를 위해)
    device_map = {"": 0} if device == "cuda" else None
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map=device_map,
        token=os.getenv("HUGGINGFACE_TOKEN"),
        trust_remote_code=True
    )

    if device != "cuda":
        model = model.to(device)

    # LoRA 설정
    print(f"\nConfiguring LoRA...")
    print(f"  r (rank): {lora_r}")
    print(f"  alpha: {lora_alpha}")
    print(f"  dropout: {lora_dropout}")

    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # Mistral/LLaMA
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )

    # LoRA 모델 생성
    model = get_peft_model(model, lora_config)

    # 학습 가능한 파라미터 수 출력
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_percent = 100 * trainable_params / total_params

    print(f"\n✓ LoRA model ready")
    print(f"  Trainable params: {trainable_params:,} ({trainable_percent:.2f}%)")
    print(f"  Total params: {total_params:,}")

    return model, tokenizer, device


def train_model(
    model,
    tokenizer,
    train_dataset,
    output_dir="models/fine-tuned/lora-mistral-custom",
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-4,
    max_length=512,
    use_mlflow=True
):
    """모델 학습"""
    print(f"\n{'='*60}")
    print("Training Model")
    print(f"{'='*60}\n")

    # MLflow 설정
    if use_mlflow and HAS_MLFLOW:
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "./mlruns"))
        experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "chatbot-finetuning")
        mlflow.set_experiment(experiment_name)

        # 실험 시작
        run_name = f"lora-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        mlflow.start_run(run_name=run_name)

        # 하이퍼파라미터 로깅
        mlflow.log_params({
            "model_name": model.config._name_or_path,
            "num_epochs": num_epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "max_length": max_length,
            "train_samples": len(train_dataset)
        })

        print(f"✓ MLflow run started: {run_name}")

    # Training arguments
    # Gradient accumulation 조정: effective batch size 유지
    gradient_accum_steps = max(1, 16 // batch_size)  # effective batch size = 16
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accum_steps,
        learning_rate=learning_rate,
        fp16=torch.cuda.is_available(),
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        report_to="mlflow" if (use_mlflow and HAS_MLFLOW) else "none",
        push_to_hub=False,
        disable_tqdm=False
    )

    print(f"  Gradient accumulation steps: {gradient_accum_steps}")
    print(f"  Effective batch size: {batch_size * gradient_accum_steps}")

    print(f"Training configuration:")
    print(f"  Output dir: {output_dir}")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  FP16: {training_args.fp16}")
    print()

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator
    )

    # 학습 시작
    print("Starting training...\n")
    train_result = trainer.train()

    # 결과 출력
    print(f"\n{'='*60}")
    print("Training Completed!")
    print(f"{'='*60}")
    print(f"Training loss: {train_result.training_loss:.4f}")
    print(f"Training time: {train_result.metrics['train_runtime']:.2f}s")
    print(f"Samples/second: {train_result.metrics['train_samples_per_second']:.2f}")

    # 모델 저장
    print(f"\nSaving model to: {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    # MLflow 로깅
    if use_mlflow and HAS_MLFLOW:
        mlflow.log_metrics({
            "train_loss": train_result.training_loss,
            "train_runtime": train_result.metrics['train_runtime'],
            "train_samples_per_second": train_result.metrics['train_samples_per_second']
        })

        # 모델 아티팩트 저장
        mlflow.log_artifact(output_dir)

        mlflow.end_run()
        print("✓ MLflow run completed")

    print(f"\n✓ Model saved successfully!")

    return trainer


def main():
    """메인 실행 함수"""
    import sys

    print("\n" + "="*60)
    print("  Phase 2-3: LoRA Fine-tuning")
    print("="*60 + "\n")

    # 설정
    model_name = os.getenv("BASE_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")

    # 커맨드라인 인자 또는 환경변수에서 설정 로드
    if len(sys.argv) > 1:
        # Non-interactive mode: use command-line arguments
        data_path = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TRAIN_DATA_PATH", "data/synthetic_train.json")
        num_epochs = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.getenv("NUM_EPOCHS", 3))
        batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else int(os.getenv("BATCH_SIZE", 4))
        learning_rate = float(sys.argv[4]) if len(sys.argv) > 4 else float(os.getenv("LEARNING_RATE", 2e-4))
        lora_r = int(sys.argv[5]) if len(sys.argv) > 5 else int(os.getenv("LORA_RANK", 16))

        print(f"Configuration (from args/env):")
        print(f"  Data path: {data_path}")
        print(f"  Epochs: {num_epochs}")
        print(f"  Batch size: {batch_size}")
        print(f"  Learning rate: {learning_rate}")
        print(f"  LoRA rank: {lora_r}")
    else:
        # Interactive mode: prompt user for input
        data_path = input("Training data path (default: data/synthetic_train.json): ").strip()
        data_path = data_path if data_path else "data/synthetic_train.json"

        # 하이퍼파라미터
        print("\nHyperparameters (press Enter for defaults):")
        num_epochs = input("  Epochs (default: 3): ").strip()
        num_epochs = int(num_epochs) if num_epochs else 3

        batch_size = input("  Batch size (default: 4): ").strip()
        batch_size = int(batch_size) if batch_size else 4

        learning_rate = input("  Learning rate (default: 2e-4): ").strip()
        learning_rate = float(learning_rate) if learning_rate else 2e-4

        lora_r = input("  LoRA rank (default: 16): ").strip()
        lora_r = int(lora_r) if lora_r else 16

    try:
        # 1. 데이터 로드
        dataset = load_training_data(data_path)

        # 2. 모델 및 토크나이저 설정
        model, tokenizer, device = setup_lora_model(
            model_name,
            lora_r=lora_r
        )

        # 3. 데이터셋 준비
        train_dataset = prepare_dataset(dataset, tokenizer, max_length=512)

        # 4. 학습
        trainer = train_model(
            model,
            tokenizer,
            train_dataset,
            num_epochs=num_epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            use_mlflow=HAS_MLFLOW
        )

        print("\n" + "="*60)
        print("Next steps:")
        print("  1. Test the fine-tuned model")
        print("  2. Try QLoRA: python src/train/02_qlora_finetune.py")
        print("  3. View experiments: mlflow ui")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
