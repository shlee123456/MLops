# src/data/ - 데이터 파이프라인

학습 데이터 준비 및 합성 데이터 생성

## 파일

| 파일 | 설명 |
|------|------|
| `01_load_dataset.py` | HuggingFace 데이터셋 로드 |
| `02_generate_synthetic_data.py` | 합성 데이터 생성 (MLOps/DevOps 특화) |

## 실행

```bash
python src/data/01_load_dataset.py           # 공개 데이터셋
python src/data/02_generate_synthetic_data.py # 합성 데이터
```

## 데이터 위치

```
data/
├── raw/                      # 원본 데이터
├── processed/                # 전처리된 데이터 (*.jsonl)
└── synthetic_train.json      # 합성 학습 데이터
```

## 데이터 형식 (Instruction)

학습에 사용되는 표준 형식:

```json
{
  "instruction": "질문/지시",
  "input": "추가 컨텍스트 (선택, 빈 문자열 가능)",
  "output": "기대 응답"
}
```

## 데이터셋 정보

| 데이터셋 | 출처 | 예시 수 |
|----------|------|---------|
| no_robots | HuggingFace | 9,499 |
| synthetic_train.json | 자체 생성 | MLOps/DevOps 특화 |
