#!/bin/bash

export HF_HUB_ENABLE_HF_TRANSFER=0
export FLASHINFER_DISABLE_VERSION_CHECK=1

python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --served-model-name qwen2.5-7b \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key test-secret-key \
  --gpu-memory-utilization 0.90 \
  --max-model-len 4096
