from setuptools import setup, find_packages

setup(
    name="mlops-chatbot",
    version="0.1.0",
    description="LLM Fine-tuning and Production Deployment MLOps Pipeline",
    author="shlee",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # requirements.txt에서 자동으로 가져옴
    ],
)
