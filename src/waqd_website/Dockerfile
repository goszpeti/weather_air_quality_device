# docker build --tag waqd_website:latest . -f src/waqd_website/Dockerfile
FROM python:3.13-alpine3.22 AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN adduser -D waqd
USER waqd
WORKDIR /home/waqd

RUN python -m venv pdm-venv && \
    . pdm-venv/bin/activate && \
    pip install --upgrade pip && \
    pip install pdm

COPY pyproject.toml pdm.lock LICENSE README.md ./
COPY src/waqd_website/__init__.py src/waqd_website/__init__.py

RUN . pdm-venv/bin/activate && pdm install --prod && \
    rm -rf ~/.cache/pdm

COPY src/waqd src/waqd
COPY src/waqd_website src/waqd_website

ENTRYPOINT ["/bin/sh", "-c", ". ./pdm-venv/bin/activate && uvicorn waqd_website.main:web_app --host 0.0.0.0 --port 8080"]
