#!/usr/bin/env bash
# Генерация Python-кода из .proto в каталог gen/
set -e
python -m grpc_tools.protoc \
  -I proto \
  --python_out=gen \
  --grpc_python_out=gen \
  proto/glossary.proto proto/recommendation.proto
echo "Сгенерировано в gen/"
