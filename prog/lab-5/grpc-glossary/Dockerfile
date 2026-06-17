FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto ./proto
COPY glossary_service ./glossary_service
COPY recommendation_service ./recommendation_service
COPY client ./client

# Генерация Python-кода из .proto при сборке образа.
RUN mkdir -p gen && python -m grpc_tools.protoc \
    -I proto --python_out=gen --grpc_python_out=gen \
    proto/glossary.proto proto/recommendation.proto

RUN mkdir -p data

# Команда по умолчанию переопределяется в docker-compose.yml.
CMD ["python", "-m", "glossary_service.server"]
