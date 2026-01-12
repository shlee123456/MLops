#!/usr/bin/env python3
"""
Phase 3-6: vLLM Server Benchmark

vLLM 서버 성능 벤치마크
처리량, 지연시간, 토큰/초 등 측정
"""

import os
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# 상대 경로 임포트
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from serve.vllm_client import VLLMClient
except ImportError:
    from vllm_client import VLLMClient

load_dotenv()


class VLLMBenchmark:
    """vLLM 성능 벤치마크"""

    def __init__(self, base_url: str = "http://localhost:8000/v1"):
        """
        Args:
            base_url: vLLM 서버 URL
        """
        self.base_url = base_url
        self.client = VLLMClient(base_url=base_url)
        self.results = []

    def check_server(self) -> bool:
        """서버 연결 확인"""
        print("Checking vLLM server connection...")
        if self.client.health_check():
            models = self.client.list_models()
            print(f"✓ Server connected. Available models: {', '.join(models)}")
            return True
        else:
            print("✗ Server not responding")
            return False

    def single_request_benchmark(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7
    ) -> Dict:
        """단일 요청 벤치마크"""
        messages = [{"role": "user", "content": prompt}]

        start_time = time.time()
        response = self.client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        elapsed_time = time.time() - start_time

        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "elapsed_time": elapsed_time
            }

        tokens = response["usage"].get("completion_tokens", 0)
        tokens_per_sec = tokens / elapsed_time if elapsed_time > 0 else 0

        return {
            "success": True,
            "elapsed_time": elapsed_time,
            "tokens": tokens,
            "tokens_per_sec": tokens_per_sec,
            "total_tokens": response["usage"].get("total_tokens", 0)
        }

    def latency_benchmark(
        self,
        num_requests: int = 10,
        max_tokens: int = 100
    ) -> Dict:
        """지연시간 벤치마크 (순차 요청)"""
        print(f"\n{'='*60}")
        print("Latency Benchmark (Sequential Requests)")
        print(f"{'='*60}\n")

        print(f"Running {num_requests} sequential requests...")
        print(f"Max tokens per request: {max_tokens}\n")

        test_prompts = [
            "What is machine learning?",
            "Explain neural networks.",
            "What is MLOps?",
            "Describe gradient descent.",
            "What is transfer learning?",
            "Explain overfitting.",
            "What is a transformer model?",
            "Describe batch normalization.",
            "What is regularization?",
            "Explain the attention mechanism."
        ]

        latencies = []
        tokens_per_sec_list = []
        successful_requests = 0

        for i in range(num_requests):
            prompt = test_prompts[i % len(test_prompts)]
            result = self.single_request_benchmark(prompt, max_tokens)

            if result["success"]:
                latencies.append(result["elapsed_time"])
                tokens_per_sec_list.append(result["tokens_per_sec"])
                successful_requests += 1
                print(f"  Request {i+1}: {result['elapsed_time']:.2f}s, "
                      f"{result['tokens_per_sec']:.1f} tokens/s")
            else:
                print(f"  Request {i+1}: FAILED - {result['error']}")

        if not latencies:
            return {"error": "All requests failed"}

        # 통계
        return {
            "num_requests": num_requests,
            "successful_requests": successful_requests,
            "latency": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "std": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "min": min(latencies),
                "max": max(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            },
            "throughput": {
                "mean_tokens_per_sec": statistics.mean(tokens_per_sec_list),
                "total_requests_per_sec": successful_requests / sum(latencies)
            }
        }

    def throughput_benchmark(
        self,
        num_requests: int = 20,
        concurrent_requests: int = 4,
        max_tokens: int = 100
    ) -> Dict:
        """처리량 벤치마크 (병렬 요청)"""
        print(f"\n{'='*60}")
        print("Throughput Benchmark (Concurrent Requests)")
        print(f"{'='*60}\n")

        print(f"Running {num_requests} total requests")
        print(f"Concurrency: {concurrent_requests}")
        print(f"Max tokens per request: {max_tokens}\n")

        test_prompts = [
            "What is deep learning?",
            "Explain reinforcement learning.",
            "What is computer vision?",
            "Describe natural language processing.",
            "What is generative AI?",
        ] * (num_requests // 5 + 1)

        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(
                    self.single_request_benchmark,
                    test_prompts[i],
                    max_tokens
                )
                futures.append(future)

            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                results.append(result)
                if result["success"]:
                    print(f"  Completed {i+1}/{num_requests}: "
                          f"{result['elapsed_time']:.2f}s, "
                          f"{result['tokens_per_sec']:.1f} tokens/s")
                else:
                    print(f"  Completed {i+1}/{num_requests}: FAILED")

        total_time = time.time() - start_time

        # 성공한 요청만 분석
        successful_results = [r for r in results if r["success"]]
        successful_count = len(successful_results)

        if successful_count == 0:
            return {"error": "All requests failed"}

        total_tokens = sum(r["tokens"] for r in successful_results)
        latencies = [r["elapsed_time"] for r in successful_results]

        return {
            "num_requests": num_requests,
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_count,
            "total_time": total_time,
            "throughput": {
                "requests_per_sec": successful_count / total_time,
                "tokens_per_sec": total_tokens / total_time,
                "mean_latency": statistics.mean(latencies),
                "median_latency": statistics.median(latencies)
            }
        }

    def stress_test(
        self,
        duration_seconds: int = 60,
        concurrent_requests: int = 8,
        max_tokens: int = 100
    ) -> Dict:
        """부하 테스트"""
        print(f"\n{'='*60}")
        print("Stress Test")
        print(f"{'='*60}\n")

        print(f"Duration: {duration_seconds} seconds")
        print(f"Concurrency: {concurrent_requests}")
        print(f"Max tokens: {max_tokens}\n")

        test_prompt = "Explain machine learning in simple terms."

        start_time = time.time()
        end_time = start_time + duration_seconds
        completed_requests = 0
        failed_requests = 0
        total_tokens = 0

        print("Running stress test...")

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []

            while time.time() < end_time:
                if len(futures) < concurrent_requests:
                    future = executor.submit(
                        self.single_request_benchmark,
                        test_prompt,
                        max_tokens
                    )
                    futures.append(future)

                # 완료된 요청 확인
                completed = [f for f in futures if f.done()]
                for future in completed:
                    result = future.result()
                    if result["success"]:
                        completed_requests += 1
                        total_tokens += result["tokens"]
                    else:
                        failed_requests += 1
                    futures.remove(future)

                time.sleep(0.01)

            # 남은 요청 처리
            for future in futures:
                result = future.result()
                if result["success"]:
                    completed_requests += 1
                    total_tokens += result["tokens"]
                else:
                    failed_requests += 1

        actual_duration = time.time() - start_time

        return {
            "duration_seconds": actual_duration,
            "concurrent_requests": concurrent_requests,
            "completed_requests": completed_requests,
            "failed_requests": failed_requests,
            "success_rate": completed_requests / (completed_requests + failed_requests) * 100,
            "throughput": {
                "requests_per_sec": completed_requests / actual_duration,
                "tokens_per_sec": total_tokens / actual_duration
            }
        }

    def save_results(self, results: Dict, output_dir: str = "results"):
        """결과 저장"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"vllm_benchmark_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Results saved to: {filename}")


def print_results(results: Dict):
    """결과 출력"""
    print(f"\n{'='*60}")
    print("Benchmark Results Summary")
    print(f"{'='*60}\n")

    for test_name, test_results in results.items():
        if test_name == "timestamp" or test_name == "server_url":
            continue

        print(f"{test_name.upper().replace('_', ' ')}:")

        if isinstance(test_results, dict):
            for key, value in test_results.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, float):
                            print(f"    {sub_key}: {sub_value:.3f}")
                        else:
                            print(f"    {sub_key}: {sub_value}")
                elif isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        print()


def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("  vLLM Server Benchmark")
    print("="*60 + "\n")

    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    benchmark = VLLMBenchmark(base_url=base_url)

    # 서버 확인
    if not benchmark.check_server():
        print("\nPlease start vLLM server first:")
        print("  python src/serve/01_vllm_server.py")
        return

    # 벤치마크 선택
    print("\nSelect benchmark type:")
    print("  1) Latency Benchmark (Sequential, 10 requests)")
    print("  2) Throughput Benchmark (Concurrent, 20 requests)")
    print("  3) Stress Test (60 seconds)")
    print("  4) Run All")

    choice = input("\nEnter choice (1-4): ").strip()

    all_results = {
        "timestamp": datetime.now().isoformat(),
        "server_url": base_url
    }

    try:
        if choice == "1" or choice == "4":
            results = benchmark.latency_benchmark(num_requests=10, max_tokens=100)
            all_results["latency_benchmark"] = results

        if choice == "2" or choice == "4":
            results = benchmark.throughput_benchmark(
                num_requests=20,
                concurrent_requests=4,
                max_tokens=100
            )
            all_results["throughput_benchmark"] = results

        if choice == "3" or choice == "4":
            results = benchmark.stress_test(
                duration_seconds=60,
                concurrent_requests=8,
                max_tokens=100
            )
            all_results["stress_test"] = results

        # 결과 출력
        print_results(all_results)

        # 결과 저장
        save = input("\nSave results to file? (y/n): ").strip().lower()
        if save == "y":
            benchmark.save_results(all_results)

    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during benchmark: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
