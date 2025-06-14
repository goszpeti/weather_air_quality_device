# docker build -f ./src/waqd_website/Dockerfile -t waqd_website:latest . --progress=plain
FROM ubuntu:24.04 AS base
 # --platform=linux/arm64 

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install python3 python3-pip python3-venv -y
#rm -rf /var/lib/apt/lists/*

RUN python3 -m venv pdm-venv && \
    . /pdm-venv/bin/activate && \
    pip install --upgrade pip && \
    pip install pdm

RUN adduser --disabled-password --gecos '' waqd 

WORKDIR /home/waqd

COPY pyproject.toml pdm.lock LICENSE README.md ./
COPY src/waqd_website/__init__.py src/waqd_website/__init__.py

RUN . /pdm-venv/bin/activate && pdm install --prod

RUN chown -R waqd:waqd /pdm-venv
RUN chown -R waqd:waqd src

USER waqd
WORKDIR /home/waqd

COPY src/waqd src/waqd
COPY src/waqd_website src/waqd_website

