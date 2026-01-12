#!/usr/bin/env python3
"""
Phase 2-4: QLoRA Fine-tuning

4-bit 양자화를 사용한 메모리 효율적인 학습
LoRA보다 ~75% 적은 메모리로 학습 가능
"""

import os
import json
import torch
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
    TrainerCallback
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.logging_utils import TrainingLogger, SystemLogger

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

load_dotenv()


class LoggingCallback(TrainerCallback):
    """Custom callback for structured logging during training"""

    def __init__(self, logger: TrainingLogger, system_logger: SystemLogger):
        self.logger = logger
        self.system_logger = system_logger
        self.current_epoch = 0

    def on_epoch_begin(self, args, state, control, **kwargs):
        """Called at the beginning of each epoch"""
        self.current_epoch = int(state.epoch) if state.epoch else 0
        self.logger.log_epoch_start(
            epoch=self.current_epoch,
            total_epochs=int(args.num_train_epochs)
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Called when logging - captures step metrics"""
        if logs:
            # Extract metrics
            loss = logs.get('loss')
            learning_rate = logs.get('learning_rate')
            epoch = logs.get('epoch', state.epoch)
            step = state.global_step

            # Log GPU metrics
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.memory_allocated() / 1e9
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1e9
                gpu_utilization = (gpu_memory_used / gpu_memory_total) * 100

                self.system_logger.log_gpu_metrics(
                    gpu_id=0,
                    gpu_memory_used=int(gpu_memory_used * 1e9),
                    gpu_memory_total=int(gpu_memory_total * 1e9),
                    gpu_utilization=gpu_utilization
                )

            # Log training step
            if loss is not None and learning_rate is not None:
                self.logger.log_step(
                    epoch=int(epoch),
                    step=step,
                    loss=loss,
                    learning_rate=learning_rate,
                    gpu_memory_gb=gpu_memory_used if torch.cuda.is_available() else 0
                )

    def on_epoch_end(self, args, state, control, **kwargs):
        """Called at the end of each epoch"""
        # Calculate average loss for the epoch
        if state.log_history:
            epoch_logs = [log for log in state.log_history if log.get('epoch', 0) >= self.current_epoch]
            losses = [log['loss'] for log in epoch_logs if 'loss' in log]
            avg_loss = sum(losses) / len(losses) if losses else 0

            self.logger.log_epoch_end(
                epoch=self.current_epoch,
                avg_loss=avg_loss
            )


def load_training_data(data_path: str):
    """학습 데이터 로드"""
    print(f"\n{'='*60}")
    print("Loading Training Data")
    print(f"{'='*60}\n")

    data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(data_path, "r") as f:
        if data_path.suffix == ".json":
            data = json.load(f)
        elif data_path.suffix == ".jsonl":
            data = [json.loads(line) for line in f]
        else:
            raise ValueError(f"Unsupported file format: {data_path.suffix}")

    print(f"✓ Loaded {len(data)} examples")

    dataset = Dataset.from_list(data)
    print(f"✓ Dataset created with {len(dataset)} examples")

    return dataset


def format_instruction(example):
    """Instruction 형식으로 포맷팅"""
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
    """데이터셋 전처리"""
    print(f"\n{'='*60}")
    print("Preparing Dataset")
    print(f"{'='*60}\n")

    print("Formatting examples...")
    dataset = dataset.map(format_instruction)

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

    print(f"✓ Dataset prepared with {len(tokenized_dataset)} examples")

    return tokenized_dataset


def setup_qlora_model(
    model_name,
    lora_r=16,
    lora_alpha=32,
    lora_dropout=0.05
):
    """QLoRA 설정 및 모델 준비 (4-bit 양자화)"""
    print(f"\n{'='*60}")
    print("Setting up QLoRA Model (4-bit)")
    print(f"{'='*60}\n")

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA requires CUDA GPU")

    print(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")

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

    # 4-bit 양자화 설정
    print("Configuring 4-bit quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )

    # 모델 로드
    print("Loading model with 4-bit quantization...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        token=os.getenv("HUGGINGFACE_TOKEN"),
        trust_remote_code=True
    )

    # 메모리 사용량 출력
    allocated = torch.cuda.memory_allocated() / 1e9
    reserved = torch.cuda.memory_reserved() / 1e9
    print(f"\nInitial GPU Memory:")
    print(f"  Allocated: {allocated:.2f} GB")
    print(f"  Reserved: {reserved:.2f} GB")

    # k-bit training 준비
    print("\nPreparing model for k-bit training...")
    model = prepare_model_for_kbit_training(model)

    # LoRA 설정
    print(f"Configuring LoRA...")
    print(f"  r (rank): {lora_r}")
    print(f"  alpha: {lora_alpha}")
    print(f"  dropout: {lora_dropout}")

    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )

    # LoRA 모델 생성
    model = get_peft_model(model, lora_config)

    # 학습 가능한 파라미터 수
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_percent = 100 * trainable_params / total_params

    print(f"\n✓ QLoRA model ready")
    print(f"  Trainable params: {trainable_params:,} ({trainable_percent:.2f}%)")
    print(f"  Total params: {total_params:,}")
    print(f"  Memory efficient: ~75% less than full LoRA")

    return model, tokenizer


def train_model(
    model,
    tokenizer,
    train_dataset,
    output_dir="models/fine-tuned/qlora-mistral-custom",
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-4,
    max_length=512,
    use_mlflow=True,
    log_dir="./logs"
):
    """모델 학습"""
    print(f"\n{'='*60}")
    print("Training Model with QLoRA")
    print(f"{'='*60}\n")

    # Initialize structured loggers
    run_name = f"qlora-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    training_logger = TrainingLogger(run_name, log_dir=log_dir)
    system_logger = SystemLogger("qlora_training", log_dir=log_dir)

    # Log training start event
    system_logger.log_event(
        "training_started",
        model_name=model.config._name_or_path,
        method="QLoRA",
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate
    )

    # MLflow 설정
    if use_mlflow and HAS_MLFLOW:
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "./mlruns"))
        experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "chatbot-finetuning")
        mlflow.set_experiment(experiment_name)

        mlflow.start_run(run_name=run_name)

        mlflow.log_params({
            "model_name": model.config._name_or_path,
            "quantization": "4-bit",
            "method": "QLoRA",
            "num_epochs": num_epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "max_length": max_length,
            "train_samples": len(train_dataset)
        })

        print(f"✓ MLflow run started: {run_name}")
        training_logger.logger.info(
            "mlflow_run_started",
            run_name=run_name,
            tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
        )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        fp16=True,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        optim="paged_adamw_32bit",  # QLoRA에 최적화된 optimizer
        report_to="mlflow" if (use_mlflow and HAS_MLFLOW) else "none",
        push_to_hub=False,
        disable_tqdm=False
    )

    print(f"Training configuration:")
    print(f"  Output dir: {output_dir}")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Optimizer: paged_adamw_32bit (QLoRA optimized)")
    print()

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )

    # Create logging callback
    logging_callback = LoggingCallback(training_logger, system_logger)

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
        callbacks=[logging_callback]
    )

    # 학습 시작
    print("Starting training...\n")
    system_logger.log_event("training_execution_started")

    try:
        train_result = trainer.train()
    except Exception as e:
        training_logger.log_error(
            error=str(e),
            traceback=True
        )
        system_logger.log_error(f"Training failed: {e}")
        raise

    # 결과 출력
    print(f"\n{'='*60}")
    print("Training Completed!")
    print(f"{'='*60}")
    print(f"Training loss: {train_result.training_loss:.4f}")
    print(f"Training time: {train_result.metrics['train_runtime']:.2f}s")
    print(f"Samples/second: {train_result.metrics['train_samples_per_second']:.2f}")

    # 최종 메모리 사용량
    allocated = torch.cuda.memory_allocated() / 1e9
    peak_allocated = torch.cuda.max_memory_allocated() / 1e9
    print(f"\nGPU Memory Usage:")
    print(f"  Current: {allocated:.2f} GB")
    print(f"  Peak: {peak_allocated:.2f} GB")

    # Log training completion
    system_logger.log_event(
        "training_completed",
        training_loss=train_result.training_loss,
        train_runtime=train_result.metrics['train_runtime'],
        samples_per_second=train_result.metrics['train_samples_per_second'],
        peak_memory_gb=peak_allocated
    )

    # 모델 저장
    print(f"\nSaving model to: {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    system_logger.log_event(
        "model_saved",
        output_dir=output_dir,
        model_size_mb=sum(f.stat().st_size for f in Path(output_dir).rglob('*') if f.is_file()) / 1e6
    )

    # MLflow 로깅
    if use_mlflow and HAS_MLFLOW:
        mlflow.log_metrics({
            "train_loss": train_result.training_loss,
            "train_runtime": train_result.metrics['train_runtime'],
            "train_samples_per_second": train_result.metrics['train_samples_per_second'],
            "peak_memory_gb": peak_allocated
        })

        mlflow.log_artifact(output_dir)
        mlflow.end_run()
        print("✓ MLflow run completed")

    print(f"\n✓ Model saved successfully!")
    print(f"\n📊 Structured logs saved to: {log_dir}/training/")

    return trainer


def main():
    """메인 실행 함수"""
    import sys

    print("\n" + "="*60)
    print("  Phase 2-4: QLoRA Fine-tuning (4-bit)")
    print("="*60 + "\n")

    # CUDA 확인
    if not torch.cuda.is_available():
        print("✗ Error: QLoRA requires CUDA GPU")
        print("\nOptions:")
        print("  1. Use GPU server/cloud")
        print("  2. Use CPU with regular LoRA: python src/train/01_lora_finetune.py")
        return

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

    # Get log directory
    log_dir = os.getenv("LOG_DIR", "./logs")

    try:
        # 1. 데이터 로드
        dataset = load_training_data(data_path)

        # 2. QLoRA 모델 설정
        model, tokenizer = setup_qlora_model(
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
            use_mlflow=HAS_MLFLOW,
            log_dir=log_dir
        )

        print("\n" + "="*60)
        print("Next steps:")
        print("  1. View logs in Grafana: http://localhost:3000")
        print("  2. Compare LoRA vs QLoRA in MLflow UI: http://localhost:5000")
        print("  3. Test the model")
        print("  4. Proceed to Phase 3: Optimization")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()

        # Log error
        error_logger = SystemLogger("qlora_error", log_dir=log_dir)
        error_logger.log_error(
            error=str(e),
            traceback=traceback.format_exc()
        )


if __name__ == "__main__":
    main()
