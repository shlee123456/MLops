#!/usr/bin/env python3
"""
Phase 3-7: LangChain Integration with vLLM

LangChain을 사용한 고급 LLM 파이프라인
RAG, 체인, 에이전트 등 구현
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# vLLM + LangChain 통합
# ============================================================

class VLLMLangChain:
    """vLLM과 LangChain 통합 클래스"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model_name: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Args:
            base_url: vLLM 서버 URL
            model_name: 모델 이름
            temperature: 샘플링 온도
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            from langchain.schema import HumanMessage, AIMessage, SystemMessage
            from langchain.memory import ConversationBufferMemory
            self.langchain_available = True
        except ImportError:
            print("⚠ LangChain not installed. Install with:")
            print("  pip install langchain langchain-openai")
            self.langchain_available = False
            return

        self.base_url = base_url
        self.temperature = temperature

        # LangChain ChatOpenAI 초기화 (vLLM과 호환)
        self.llm = ChatOpenAI(
            openai_api_key="EMPTY",
            openai_api_base=base_url,
            model_name=model_name or "vllm-model",
            temperature=temperature
        )

        print(f"✓ VLLMLangChain initialized")
        print(f"  Base URL: {base_url}")
        print(f"  Temperature: {temperature}")

    def simple_chat(self, message: str) -> str:
        """간단한 채팅"""
        if not self.langchain_available:
            return "LangChain not available"

        from langchain.schema import HumanMessage

        response = self.llm.invoke([HumanMessage(content=message)])
        return response.content

    def chat_with_history(
        self,
        message: str,
        system_prompt: str = "You are a helpful AI assistant."
    ) -> str:
        """대화 기록을 포함한 채팅"""
        if not self.langchain_available:
            return "LangChain not available"

        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain.schema.runnable import RunnablePassthrough
        from langchain.memory import ConversationBufferMemory

        # 프롬프트 템플릿
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # 메모리
        memory = ConversationBufferMemory(return_messages=True)

        # 체인 구성
        chain = prompt | self.llm

        # 실행
        response = chain.invoke({
            "input": message,
            "history": memory.load_memory_variables({})["history"]
        })

        return response.content

    def create_qa_chain(self, system_prompt: str = None):
        """Q&A 체인 생성"""
        if not self.langchain_available:
            return None

        from langchain.prompts import ChatPromptTemplate
        from langchain.schema.output_parser import StrOutputParser

        system_prompt = system_prompt or "You are a helpful AI assistant. Answer questions clearly and concisely."

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        return chain

    def create_rag_chain(self, documents: List[str]):
        """RAG (Retrieval-Augmented Generation) 체인"""
        if not self.langchain_available:
            return None

        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain.vectorstores import FAISS
            from langchain.embeddings import HuggingFaceEmbeddings
            from langchain.prompts import ChatPromptTemplate
            from langchain.schema.output_parser import StrOutputParser
            from langchain.schema.runnable import RunnablePassthrough
        except ImportError:
            print("⚠ Additional packages needed for RAG:")
            print("  pip install faiss-cpu sentence-transformers")
            return None

        # 문서 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        splits = text_splitter.create_documents(documents)

        # 벡터 스토어 생성
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        vectorstore = FAISS.from_documents(splits, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # RAG 프롬프트
        prompt = ChatPromptTemplate.from_template("""
Answer the question based on the following context:

Context:
{context}

Question: {question}

Answer:""")

        # RAG 체인
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain


# ============================================================
# 사용 예제
# ============================================================

def example_simple_chat():
    """간단한 채팅 예제"""
    print("\n" + "="*60)
    print("Example 1: Simple Chat")
    print("="*60 + "\n")

    vllm = VLLMLangChain()

    questions = [
        "What is MLOps?",
        "Explain the difference between Docker and Kubernetes.",
        "What are the benefits of model versioning?"
    ]

    for question in questions:
        print(f"Q: {question}")
        response = vllm.simple_chat(question)
        print(f"A: {response}\n")


def example_qa_chain():
    """Q&A 체인 예제"""
    print("\n" + "="*60)
    print("Example 2: Q&A Chain")
    print("="*60 + "\n")

    vllm = VLLMLangChain()

    # MLOps 전문 Q&A 체인
    system_prompt = """You are an expert MLOps engineer. Provide clear, practical answers
about machine learning operations, deployment, and best practices."""

    qa_chain = vllm.create_qa_chain(system_prompt)

    if qa_chain:
        questions = [
            "How do I monitor model drift in production?",
            "What's the best way to version training data?",
            "Explain blue-green deployment for ML models."
        ]

        for question in questions:
            print(f"Q: {question}")
            response = qa_chain.invoke({"question": question})
            print(f"A: {response}\n")


def example_rag():
    """RAG 예제"""
    print("\n" + "="*60)
    print("Example 3: RAG (Retrieval-Augmented Generation)")
    print("="*60 + "\n")

    vllm = VLLMLangChain()

    # 샘플 문서
    documents = [
        """
        MLOps (Machine Learning Operations) is a set of practices that combines
        Machine Learning, DevOps, and Data Engineering. It aims to deploy and
        maintain ML models in production reliably and efficiently.
        """,
        """
        Model monitoring is crucial in MLOps. It involves tracking model performance
        metrics, data drift, and concept drift. Tools like Prometheus and Grafana
        are commonly used for monitoring ML systems.
        """,
        """
        CI/CD for ML involves automating the training, testing, and deployment of
        ML models. This includes automated testing of model quality, data validation,
        and deployment pipelines using tools like Jenkins, GitLab CI, or GitHub Actions.
        """,
        """
        Feature stores are centralized repositories for storing and serving features
        for ML models. They help maintain consistency between training and serving,
        and enable feature reuse across different models.
        """
    ]

    rag_chain = vllm.create_rag_chain(documents)

    if rag_chain:
        questions = [
            "What is MLOps?",
            "How do we monitor ML models?",
            "What are feature stores?"
        ]

        for question in questions:
            print(f"Q: {question}")
            response = rag_chain.invoke(question)
            print(f"A: {response}\n")


def example_conversation():
    """대화 예제"""
    print("\n" + "="*60)
    print("Example 4: Conversation with Memory")
    print("="*60 + "\n")

    vllm = VLLMLangChain()

    system_prompt = "You are a helpful AI assistant. Remember the context of our conversation."

    conversation = [
        "My name is Alice.",
        "What's my name?",
        "I'm interested in MLOps.",
        "What topics should I learn based on my interest?"
    ]

    for message in conversation:
        print(f"User: {message}")
        response = vllm.chat_with_history(message, system_prompt)
        print(f"Assistant: {response}\n")


# ============================================================
# 고급 파이프라인
# ============================================================

def create_code_review_pipeline():
    """코드 리뷰 파이프라인"""
    print("\n" + "="*60)
    print("Advanced: Code Review Pipeline")
    print("="*60 + "\n")

    vllm = VLLMLangChain()

    system_prompt = """You are a senior software engineer conducting code review.
Analyze the code and provide:
1. Security issues
2. Performance concerns
3. Best practice violations
4. Improvement suggestions"""

    qa_chain = vllm.create_qa_chain(system_prompt)

    if qa_chain:
        code = """
def process_user_input(user_input):
    query = "SELECT * FROM users WHERE username = '" + user_input + "'"
    result = execute_query(query)
    return result
"""

        question = f"Review this Python code:\n\n{code}"
        response = qa_chain.invoke({"question": question})
        print(f"Code Review:\n{response}\n")


# ============================================================
# Main
# ============================================================

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("  LangChain + vLLM Integration Demo")
    print("="*60 + "\n")

    print("Make sure vLLM server is running:")
    print("  python src/serve/01_vllm_server.py\n")

    print("Select example to run:")
    print("  1) Simple Chat")
    print("  2) Q&A Chain")
    print("  3) RAG (Retrieval-Augmented Generation)")
    print("  4) Conversation with Memory")
    print("  5) Code Review Pipeline")
    print("  6) Run All Examples")

    choice = input("\nEnter choice (1-6): ").strip()

    try:
        if choice == "1" or choice == "6":
            example_simple_chat()

        if choice == "2" or choice == "6":
            example_qa_chain()

        if choice == "3" or choice == "6":
            example_rag()

        if choice == "4" or choice == "6":
            example_conversation()

        if choice == "5" or choice == "6":
            create_code_review_pipeline()

        print("\n" + "="*60)
        print("✓ Demo completed!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
