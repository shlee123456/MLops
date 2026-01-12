#!/usr/bin/env python3
"""
Phase 3-2: vLLM API Client

vLLM 서버와 통신하는 클라이언트
OpenAI Python SDK 호환
"""

import os
import json
import time
from typing import List, Dict, Optional, Generator
from dotenv import load_dotenv

load_dotenv()


class VLLMClient:
    """vLLM OpenAI-compatible API 클라이언트"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
        timeout: int = 60
    ):
        """
        Args:
            base_url: vLLM 서버 베이스 URL
            api_key: API 키 (vLLM은 기본적으로 불필요)
            timeout: 요청 타임아웃 (초)
        """
        try:
            from openai import OpenAI
            self.openai_available = True
        except ImportError:
            self.openai_available = False
            print("⚠ OpenAI SDK not found. Using requests library instead.")
            import requests
            self.requests = requests

        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

        if self.openai_available:
            # OpenAI SDK 사용
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout
            )
        else:
            # requests 사용
            self.client = None

        print(f"✓ VLLMClient initialized")
        print(f"  Base URL: {base_url}")

    def list_models(self) -> List[str]:
        """사용 가능한 모델 목록 조회"""
        if self.openai_available:
            try:
                models = self.client.models.list()
                return [model.id for model in models.data]
            except Exception as e:
                print(f"✗ Error listing models: {e}")
                return []
        else:
            # requests 사용
            try:
                response = self.requests.get(
                    f"{self.base_url}/models",
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            except Exception as e:
                print(f"✗ Error listing models: {e}")
                return []

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """
        채팅 완성 요청

        Args:
            messages: 대화 메시지 리스트
                [{"role": "user", "content": "Hello"}]
            model: 모델 이름 (생략 시 서버 기본값)
            temperature: 샘플링 온도
            max_tokens: 최대 생성 토큰
            top_p: Top-p 샘플링
            stream: 스트리밍 모드
            **kwargs: 기타 파라미터

        Returns:
            응답 딕셔너리 또는 스트림 제너레이터
        """
        if model is None:
            # 첫 번째 모델 사용
            models = self.list_models()
            model = models[0] if models else "unknown"

        if self.openai_available:
            # OpenAI SDK 사용
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    stream=stream,
                    **kwargs
                )

                if stream:
                    return self._stream_response(response)
                else:
                    return {
                        "content": response.choices[0].message.content,
                        "model": response.model,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        },
                        "finish_reason": response.choices[0].finish_reason
                    }
            except Exception as e:
                print(f"✗ Error in chat completion: {e}")
                return {"error": str(e)}
        else:
            # requests 사용
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "stream": stream,
                    **kwargs
                }

                response = self.requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                    stream=stream
                )
                response.raise_for_status()

                if stream:
                    return self._stream_response_requests(response)
                else:
                    data = response.json()
                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "model": data["model"],
                        "usage": data.get("usage", {}),
                        "finish_reason": data["choices"][0].get("finish_reason")
                    }
            except Exception as e:
                print(f"✗ Error in chat completion: {e}")
                return {"error": str(e)}

    def _stream_response(self, response) -> Generator[str, None, None]:
        """OpenAI SDK 스트림 응답 처리"""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def _stream_response_requests(self, response) -> Generator[str, None, None]:
        """requests 스트림 응답 처리"""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(line)
                        if data["choices"][0]["delta"].get("content"):
                            yield data["choices"][0]["delta"]["content"]
                    except json.JSONDecodeError:
                        continue

    def completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> Dict:
        """
        텍스트 완성 요청

        Args:
            prompt: 프롬프트 텍스트
            model: 모델 이름
            temperature: 샘플링 온도
            max_tokens: 최대 생성 토큰
            **kwargs: 기타 파라미터

        Returns:
            응답 딕셔너리
        """
        if model is None:
            models = self.list_models()
            model = models[0] if models else "unknown"

        if self.openai_available:
            try:
                response = self.client.completions.create(
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                return {
                    "content": response.choices[0].text,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            except Exception as e:
                print(f"✗ Error in completion: {e}")
                return {"error": str(e)}
        else:
            # requests 사용
            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }

                response = self.requests.post(
                    f"{self.base_url}/completions",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()
                return {
                    "content": data["choices"][0]["text"],
                    "model": data["model"],
                    "usage": data.get("usage", {})
                }
            except Exception as e:
                print(f"✗ Error in completion: {e}")
                return {"error": str(e)}

    def health_check(self) -> bool:
        """서버 헬스 체크"""
        if self.openai_available:
            try:
                models = self.list_models()
                return len(models) > 0
            except:
                return False
        else:
            try:
                response = self.requests.get(
                    f"{self.base_url.replace('/v1', '')}/health",
                    timeout=5
                )
                return response.status_code == 200
            except:
                return False


def test_client():
    """클라이언트 테스트"""
    print("\n" + "="*60)
    print("  vLLM Client Test")
    print("="*60 + "\n")

    # 클라이언트 초기화
    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    client = VLLMClient(base_url=base_url)

    # 헬스 체크
    print("1. Health Check")
    if client.health_check():
        print("  ✓ Server is healthy\n")
    else:
        print("  ✗ Server is not responding")
        print("  Make sure vLLM server is running:")
        print("    python src/serve/01_vllm_server.py\n")
        return

    # 모델 목록
    print("2. List Models")
    models = client.list_models()
    for model in models:
        print(f"  - {model}")
    print()

    # 채팅 완성
    print("3. Chat Completion (Non-streaming)")
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What is MLOps? Explain in 2-3 sentences."}
    ]

    start_time = time.time()
    response = client.chat_completion(
        messages=messages,
        max_tokens=200,
        temperature=0.7
    )
    elapsed_time = time.time() - start_time

    if "error" not in response:
        print(f"  Response: {response['content'][:200]}...")
        print(f"  Model: {response['model']}")
        print(f"  Tokens: {response['usage'].get('total_tokens', 'N/A')}")
        print(f"  Time: {elapsed_time:.2f}s")
    else:
        print(f"  Error: {response['error']}")
    print()

    # 스트리밍
    print("4. Chat Completion (Streaming)")
    messages = [
        {"role": "user", "content": "Count from 1 to 5 slowly."}
    ]

    print("  Response: ", end="", flush=True)
    start_time = time.time()
    stream = client.chat_completion(
        messages=messages,
        max_tokens=100,
        stream=True
    )

    for chunk in stream:
        print(chunk, end="", flush=True)

    elapsed_time = time.time() - start_time
    print(f"\n  Time: {elapsed_time:.2f}s")
    print()

    print("="*60)
    print("✓ Client test completed!")
    print("="*60 + "\n")


def main():
    """메인 실행 함수"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_client()
    else:
        print("Usage:")
        print("  python src/serve/02_vllm_client.py test")
        print("\nOr import in your code:")
        print("  from src.serve.vllm_client import VLLMClient")
        print("  client = VLLMClient()")
        print("  response = client.chat_completion(messages=[...])")


if __name__ == "__main__":
    main()
