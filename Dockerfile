FROM python:3.11.9-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR app/

RUN apt-get update
RUN pip install --upgrade pip

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY financefacile ./
