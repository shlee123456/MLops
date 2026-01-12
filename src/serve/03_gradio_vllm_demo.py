#!/usr/bin/env python3
"""
Phase 3-3: Gradio vLLM Demo

vLLM 서버와 연결된 Gradio 웹 인터페이스
"""

import os
import time
import gradio as gr
from dotenv import load_dotenv
from typing import List, Tuple

# 상대 경로 임포트를 위한 경로 추가
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from serve.vllm_client import VLLMClient
except ImportError:
    # 직접 실행 시
    from vllm_client import VLLMClient

load_dotenv()


class GradioVLLMInterface:
    """Gradio vLLM 인터페이스"""

    def __init__(self, base_url: str = "http://localhost:8000/v1"):
        """
        Args:
            base_url: vLLM 서버 URL
        """
        self.base_url = base_url
        self.client = None
        self.available_models = []

    def initialize_client(self):
        """클라이언트 초기화"""
        try:
            self.client = VLLMClient(base_url=self.base_url)

            # 헬스 체크
            if not self.client.health_check():
                return False, "⚠ vLLM 서버가 응답하지 않습니다. 서버를 먼저 실행해주세요."

            # 모델 목록 가져오기
            self.available_models = self.client.list_models()

            if not self.available_models:
                return False, "⚠ 사용 가능한 모델이 없습니다."

            return True, f"✓ vLLM 서버 연결 성공! (Models: {', '.join(self.available_models)})"

        except Exception as e:
            return False, f"✗ 연결 실패: {e}"

    def chat(
        self,
        message: str,
        history: List[Tuple[str, str]],
        system_prompt: str,
        model_name: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stream: bool
    ):
        """
        채팅 응답 생성

        Args:
            message: 사용자 메시지
            history: 대화 기록
            system_prompt: 시스템 프롬프트
            model_name: 모델 이름
            max_tokens: 최대 토큰
            temperature: 온도
            top_p: Top-p
            stream: 스트리밍 여부
        """
        if self.client is None:
            yield "⚠ 클라이언트가 초기화되지 않았습니다. 'Connect to Server' 버튼을 먼저 클릭하세요."
            return

        # 메시지 구성
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 대화 기록 추가
        for user_msg, bot_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})

        # 현재 메시지 추가
        messages.append({"role": "user", "content": message})

        # 스트리밍 모드
        if stream:
            response_text = ""
            try:
                stream_response = self.client.chat_completion(
                    messages=messages,
                    model=model_name if model_name != "auto" else None,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stream=True
                )

                for chunk in stream_response:
                    response_text += chunk
                    yield response_text

            except Exception as e:
                yield f"✗ 에러: {e}"

        # 일반 모드
        else:
            try:
                response = self.client.chat_completion(
                    messages=messages,
                    model=model_name if model_name != "auto" else None,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stream=False
                )

                if "error" in response:
                    yield f"✗ 에러: {response['error']}"
                else:
                    yield response["content"]

            except Exception as e:
                yield f"✗ 에러: {e}"


def create_interface():
    """Gradio 인터페이스 생성"""

    interface = GradioVLLMInterface()

    with gr.Blocks(title="vLLM Chatbot Demo", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🚀 vLLM Chatbot Demo

            고성능 vLLM 서버와 연결된 채팅 인터페이스
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                # 연결 상태
                with gr.Group():
                    gr.Markdown("### 서버 연결")
                    server_url = gr.Textbox(
                        label="vLLM Server URL",
                        value=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
                        placeholder="http://localhost:8000/v1"
                    )
                    connect_btn = gr.Button("Connect to Server", variant="primary")
                    connection_status = gr.Textbox(
                        label="Connection Status",
                        value="Not connected",
                        interactive=False
                    )

                # 시스템 프롬프트
                with gr.Group():
                    gr.Markdown("### 시스템 설정")
                    system_prompt = gr.Textbox(
                        label="System Prompt",
                        value="You are a helpful AI assistant specialized in MLOps and DevOps.",
                        lines=3,
                        placeholder="시스템 프롬프트를 입력하세요..."
                    )
                    model_dropdown = gr.Dropdown(
                        label="Model",
                        choices=["auto"],
                        value="auto",
                        interactive=True
                    )

            with gr.Column(scale=2):
                # 생성 파라미터
                with gr.Group():
                    gr.Markdown("### 생성 파라미터")

                    max_tokens = gr.Slider(
                        minimum=50,
                        maximum=2048,
                        value=512,
                        step=1,
                        label="Max Tokens",
                        info="생성할 최대 토큰 수"
                    )

                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="Temperature",
                        info="높을수록 창의적, 낮을수록 결정적"
                    )

                    top_p = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.9,
                        step=0.05,
                        label="Top-p",
                        info="누적 확률 임계값"
                    )

                    stream_checkbox = gr.Checkbox(
                        label="Enable Streaming",
                        value=True,
                        info="스트리밍 모드 (실시간 응답)"
                    )

        # 채팅 인터페이스
        gr.Markdown("### 💬 Chat")

        chatbot = gr.Chatbot(
            label="Conversation",
            height=400,
            show_copy_button=True
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Your Message",
                placeholder="메시지를 입력하세요...",
                lines=2,
                scale=4
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("Clear Chat")

        # 예제
        gr.Examples(
            examples=[
                ["What is MLOps and why is it important?"],
                ["Explain the difference between LoRA and QLoRA fine-tuning."],
                ["How do I set up a CI/CD pipeline for ML models?"],
                ["Write a Python function to calculate accuracy metrics."],
                ["What are the best practices for model monitoring in production?"]
            ],
            inputs=msg,
            label="Example Questions"
        )

        # 이벤트 핸들러
        def update_connection(url):
            """서버 연결"""
            interface.base_url = url
            success, message = interface.initialize_client()

            if success:
                # 모델 목록 업데이트
                models = ["auto"] + interface.available_models
                return message, gr.Dropdown(choices=models, value="auto")
            else:
                return message, gr.Dropdown(choices=["auto"], value="auto")

        def respond(message, chat_history, system, model, max_tok, temp, top, strm):
            """채팅 응답"""
            # 응답 생성
            bot_message = interface.chat(
                message=message,
                history=chat_history,
                system_prompt=system,
                model_name=model,
                max_tokens=max_tok,
                temperature=temp,
                top_p=top,
                stream=strm
            )

            # 스트리밍인 경우
            if strm:
                chat_history.append([message, ""])
                for response in bot_message:
                    chat_history[-1][1] = response
                    yield "", chat_history
            else:
                # 일반 모드
                response = next(bot_message)
                chat_history.append([message, response])
                yield "", chat_history

        # 버튼 연결
        connect_btn.click(
            fn=update_connection,
            inputs=[server_url],
            outputs=[connection_status, model_dropdown]
        )

        send_btn.click(
            fn=respond,
            inputs=[
                msg, chatbot, system_prompt, model_dropdown,
                max_tokens, temperature, top_p, stream_checkbox
            ],
            outputs=[msg, chatbot]
        )

        msg.submit(
            fn=respond,
            inputs=[
                msg, chatbot, system_prompt, model_dropdown,
                max_tokens, temperature, top_p, stream_checkbox
            ],
            outputs=[msg, chatbot]
        )

        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, msg]
        )

        gr.Markdown(
            """
            ---
            ### 사용 방법

            1. **서버 시작**: vLLM 서버를 먼저 실행하세요
               ```bash
               python src/serve/01_vllm_server.py
               ```

            2. **연결**: 'Connect to Server' 버튼 클릭

            3. **채팅**: 메시지를 입력하고 Send 버튼 클릭

            ### 팁
            - 스트리밍 모드는 실시간 응답을 제공합니다
            - Temperature를 낮추면 더 일관된 응답을 얻을 수 있습니다
            - System Prompt를 수정하여 AI의 역할을 변경할 수 있습니다
            """
        )

    return demo


def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("  Gradio vLLM Demo")
    print("="*60 + "\n")

    print("Starting Gradio interface...")
    print("\nMake sure vLLM server is running:")
    print("  python src/serve/01_vllm_server.py")
    print()

    demo = create_interface()

    # 서버 시작
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
