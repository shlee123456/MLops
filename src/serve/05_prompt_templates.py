#!/usr/bin/env python3
"""
Phase 3-5: Prompt Templates and Engineering

프롬프트 템플릿 관리 및 최적화
다양한 태스크별 프롬프트 제공
"""

from typing import Dict, List, Optional
from enum import Enum


class PromptType(Enum):
    """프롬프트 타입"""
    GENERAL = "general"
    MLOPS = "mlops"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    EXPLANATION = "explanation"
    SUMMARY = "summary"
    QA = "qa"


class PromptTemplate:
    """프롬프트 템플릿 클래스"""

    # ============================================================
    # System Prompts
    # ============================================================

    SYSTEM_PROMPTS = {
        PromptType.GENERAL: """You are a helpful AI assistant. Provide clear, accurate, and concise responses.""",

        PromptType.MLOPS: """You are an expert MLOps engineer with deep knowledge of:
- Machine Learning model development and deployment
- CI/CD pipelines for ML systems
- Model monitoring and observability
- Infrastructure as Code (Terraform, Kubernetes)
- Containerization (Docker)
- ML frameworks (PyTorch, TensorFlow, HuggingFace)
- Experiment tracking (MLflow, Weights & Biases)
- Model serving (vLLM, TorchServe, FastAPI)

Provide practical, production-ready advice with code examples when appropriate.""",

        PromptType.CODE_GENERATION: """You are an expert software engineer. Generate clean, well-documented, and efficient code.
Follow best practices:
- Write clear variable and function names
- Add helpful comments
- Include error handling
- Follow PEP 8 for Python
- Provide usage examples""",

        PromptType.CODE_REVIEW: """You are a senior software engineer conducting code review. Analyze code for:
- Correctness and logic errors
- Security vulnerabilities
- Performance issues
- Code style and best practices
- Potential bugs
- Improvement suggestions

Be constructive and specific in your feedback.""",

        PromptType.DEBUGGING: """You are a debugging expert. Help identify and fix issues by:
- Analyzing error messages and stack traces
- Identifying root causes
- Suggesting specific fixes
- Explaining why the error occurred
- Recommending prevention strategies""",

        PromptType.EXPLANATION: """You are a technical educator. Explain concepts clearly:
- Start with high-level overview
- Break down complex topics
- Use analogies and examples
- Provide visual descriptions if helpful
- Adapt to the user's knowledge level""",

        PromptType.SUMMARY: """You are a technical writer specializing in summarization. Create concise summaries that:
- Capture key points
- Maintain technical accuracy
- Use clear structure
- Highlight important details
- Keep appropriate length""",

        PromptType.QA: """You are a knowledgeable assistant answering questions. Provide:
- Direct answers to the question
- Supporting explanation
- Examples when helpful
- References or further reading if relevant
- Admission if uncertain"""
    }

    # ============================================================
    # Task-Specific Templates
    # ============================================================

    TASK_TEMPLATES = {
        "mlops_deployment": """I need help deploying a machine learning model. Here are the details:

Model: {model_type}
Framework: {framework}
Scale: {scale}
Requirements: {requirements}

Please provide a step-by-step deployment plan including infrastructure, serving, and monitoring.""",

        "code_explanation": """Please explain the following code:

```{language}
{code}
```

Focus on: {focus_areas}""",

        "code_generation": """Write a {language} {code_type} that:

Requirements:
{requirements}

Include:
- Function/class implementation
- Documentation
- Usage example
- Error handling""",

        "debugging_help": """I'm encountering this error:

```
{error_message}
```

Code context:
```{language}
{code}
```

Environment: {environment}

Please help me debug and fix this issue.""",

        "optimization": """Optimize the following code for {optimization_target}:

```{language}
{code}
```

Constraints: {constraints}""",

        "review_code": """Please review this code:

```{language}
{code}
```

Review focus:
{focus_areas}""",

        "mlops_architecture": """Design an MLOps architecture for:

Project: {project_description}
Scale: {scale}
Team size: {team_size}
Constraints: {constraints}

Include: data pipeline, training, deployment, monitoring.""",

        "troubleshooting": """I'm facing this issue:

Problem: {problem_description}
System: {system_info}
What I've tried: {attempted_solutions}

Please help troubleshoot."""
    }

    # ============================================================
    # Few-Shot Examples
    # ============================================================

    FEW_SHOT_EXAMPLES = {
        "mlops_qa": [
            {
                "role": "user",
                "content": "What's the difference between model versioning and data versioning?"
            },
            {
                "role": "assistant",
                "content": """Model versioning and data versioning serve different purposes in MLOps:

**Model Versioning:**
- Tracks different iterations of trained models
- Includes model weights, architecture, hyperparameters
- Tools: MLflow, DVC, W&B
- Enables: rollback, A/B testing, model comparison

**Data Versioning:**
- Tracks changes in training/validation datasets
- Includes data snapshots, transformations
- Tools: DVC, Delta Lake, Pachyderm
- Enables: reproducibility, data lineage tracking

Both are crucial for ML reproducibility and should be used together."""
            }
        ],

        "code_generation": [
            {
                "role": "user",
                "content": "Write a function to calculate F1 score"
            },
            {
                "role": "assistant",
                "content": """```python
def calculate_f1_score(precision: float, recall: float) -> float:
    \"\"\"
    Calculate F1 score from precision and recall.

    Args:
        precision: Precision value (0.0 to 1.0)
        recall: Recall value (0.0 to 1.0)

    Returns:
        F1 score (harmonic mean of precision and recall)

    Raises:
        ValueError: If precision or recall is invalid
    \"\"\"
    if not (0 <= precision <= 1 and 0 <= recall <= 1):
        raise ValueError("Precision and recall must be between 0 and 1")

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)

# Usage example
precision = 0.85
recall = 0.75
f1 = calculate_f1_score(precision, recall)
print(f"F1 Score: {f1:.3f}")  # Output: F1 Score: 0.797
```"""
            }
        ]
    }

    # ============================================================
    # Methods
    # ============================================================

    @classmethod
    def get_system_prompt(cls, prompt_type: PromptType) -> str:
        """시스템 프롬프트 가져오기"""
        return cls.SYSTEM_PROMPTS.get(prompt_type, cls.SYSTEM_PROMPTS[PromptType.GENERAL])

    @classmethod
    def get_task_template(cls, task_name: str) -> Optional[str]:
        """태스크 템플릿 가져오기"""
        return cls.TASK_TEMPLATES.get(task_name)

    @classmethod
    def format_template(cls, task_name: str, **kwargs) -> Optional[str]:
        """템플릿 포맷팅"""
        template = cls.get_task_template(task_name)
        if template is None:
            return None

        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"Missing template variable: {e}")
            return None

    @classmethod
    def build_messages(
        cls,
        user_message: str,
        prompt_type: PromptType = PromptType.GENERAL,
        include_examples: bool = False,
        example_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        메시지 리스트 빌드

        Args:
            user_message: 사용자 메시지
            prompt_type: 프롬프트 타입
            include_examples: Few-shot 예제 포함 여부
            example_type: 예제 타입

        Returns:
            메시지 리스트
        """
        messages = []

        # System prompt
        system_prompt = cls.get_system_prompt(prompt_type)
        messages.append({"role": "system", "content": system_prompt})

        # Few-shot examples
        if include_examples and example_type:
            examples = cls.FEW_SHOT_EXAMPLES.get(example_type, [])
            messages.extend(examples)

        # User message
        messages.append({"role": "user", "content": user_message})

        return messages

    @classmethod
    def list_templates(cls) -> Dict[str, List[str]]:
        """사용 가능한 템플릿 목록"""
        return {
            "system_prompts": [pt.value for pt in PromptType],
            "task_templates": list(cls.TASK_TEMPLATES.keys()),
            "few_shot_examples": list(cls.FEW_SHOT_EXAMPLES.keys())
        }


# ============================================================
# Utility Functions
# ============================================================

def create_mlops_chat_prompt(question: str) -> List[Dict[str, str]]:
    """MLOps 질문을 위한 프롬프트 생성"""
    return PromptTemplate.build_messages(
        user_message=question,
        prompt_type=PromptType.MLOPS,
        include_examples=True,
        example_type="mlops_qa"
    )


def create_code_gen_prompt(
    description: str,
    language: str = "python",
    requirements: List[str] = None
) -> List[Dict[str, str]]:
    """코드 생성을 위한 프롬프트 생성"""
    requirements_str = "\n".join(f"- {req}" for req in (requirements or []))

    user_message = PromptTemplate.format_template(
        "code_generation",
        language=language,
        code_type=description,
        requirements=requirements_str or "None specified"
    )

    return PromptTemplate.build_messages(
        user_message=user_message,
        prompt_type=PromptType.CODE_GENERATION,
        include_examples=True,
        example_type="code_generation"
    )


def create_debugging_prompt(
    error_message: str,
    code: str,
    language: str = "python",
    environment: str = "Python 3.10"
) -> List[Dict[str, str]]:
    """디버깅을 위한 프롬프트 생성"""
    user_message = PromptTemplate.format_template(
        "debugging_help",
        error_message=error_message,
        code=code,
        language=language,
        environment=environment
    )

    return PromptTemplate.build_messages(
        user_message=user_message,
        prompt_type=PromptType.DEBUGGING
    )


# ============================================================
# Example Usage
# ============================================================

def main():
    """메인 실행 함수 - 예제"""
    print("\n" + "="*60)
    print("  Prompt Templates Demo")
    print("="*60 + "\n")

    # 1. 사용 가능한 템플릿 목록
    print("1. Available Templates:")
    templates = PromptTemplate.list_templates()
    for category, items in templates.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")

    # 2. MLOps 질문 프롬프트
    print("\n" + "="*60)
    print("2. MLOps Question Prompt Example:")
    print("="*60)

    messages = create_mlops_chat_prompt("What is model drift and how do we detect it?")
    for msg in messages:
        print(f"\n[{msg['role'].upper()}]")
        print(msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content'])

    # 3. 코드 생성 프롬프트
    print("\n" + "="*60)
    print("3. Code Generation Prompt Example:")
    print("="*60)

    messages = create_code_gen_prompt(
        description="function to load and preprocess images",
        language="python",
        requirements=[
            "Support multiple image formats (jpg, png)",
            "Resize images to specified dimensions",
            "Normalize pixel values",
            "Handle errors gracefully"
        ]
    )

    for msg in messages:
        print(f"\n[{msg['role'].upper()}]")
        print(msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content'])

    print("\n" + "="*60)
    print("✓ Demo completed!")
    print("\nUsage in your code:")
    print("  from src.serve.prompt_templates import PromptTemplate, create_mlops_chat_prompt")
    print("  messages = create_mlops_chat_prompt('Your question here')")
    print("  # Use messages with vLLM client")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
