FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow kaggle

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1
