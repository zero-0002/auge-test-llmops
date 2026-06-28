# LLMOps Test Project — Qwen2.5-7B-Instruct on vLLM

## Candidate

Araki Ren
Role: LLMOps Engineer

## Overview

This project demonstrates a production-style LLM serving prototype using an open-source instruction model served with vLLM.

The prototype focuses on practical LLMOps skills:

* serving an open-source LLM with a production-ready engine
* exposing an OpenAI-compatible API
* API-key authentication
* health-check validation
* streaming response support
* GPU-based inference
* performance/load testing
* environment troubleshooting and operational documentation

The model server was successfully started and tested locally. External testing from Postman requires the GPU provider or container platform to expose port `8000`, or alternatively an SSH tunnel/provider proxy URL can be used.

---

## Model

Selected model:

```text
Qwen/Qwen2.5-7B-Instruct
```

Served model name:

```text
qwen2.5-7b
```

### Why this model

Qwen2.5-7B-Instruct was selected because it is an open-source instruction-following model that is practical for a single 24GB GPU environment. It is large enough to demonstrate real LLM serving behavior while remaining feasible for a short LLMOps test.

---

## Runtime Environment

Observed environment:

```text
GPU: NVIDIA GeForce RTX 4090
VRAM: 24GB
Driver Version: 570.195.03
CUDA Supported by Driver: 12.8
Python: 3.12.3
Serving Engine: vLLM
API Format: OpenAI-compatible API
Authentication: Bearer API key
```

---

## Architecture

```text
Client / curl / Postman
        ↓
vLLM OpenAI-Compatible API Server
        ↓
Qwen2.5-7B-Instruct
        ↓
NVIDIA RTX 4090 GPU
```

The current implementation uses vLLM directly as the OpenAI-compatible API server.

---

## Start the Server

```bash
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
```

---

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```text
OK
```

---

## Chat Completion Test

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer test-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b",
    "messages": [
      {
        "role": "user",
        "content": "Explain LLMOps in 3 sentences."
      }
    ],
    "temperature": 0.2,
    "max_tokens": 200
  }'
```

---

## Postman Test

Method:

```text
POST
```

URL:

```text
http://SERVER_PUBLIC_IP:8000/v1/chat/completions
```

Headers:

```text
Authorization: Bearer test-secret-key
Content-Type: application/json
```

Body:

```json
{
  "model": "qwen2.5-7b",
  "messages": [
    {
      "role": "user",
      "content": "Explain LLMOps in 3 sentences."
    }
  ],
  "temperature": 0.2,
  "max_tokens": 200
}
```

If public access fails, use an SSH tunnel:

```bash
ssh -L 8000:localhost:8000 root@SERVER_PUBLIC_IP
```

Then use:

```text
http://localhost:8000/v1/chat/completions
```

---

## Performance Results

Benchmark conditions:

```text
GPU: NVIDIA RTX 4090 24GB
Driver: 570.195.03
CUDA supported by driver: 12.8
Model: Qwen/Qwen2.5-7B-Instruct
Serving engine: vLLM
Max model length: 4096
GPU memory utilization: 0.90
```

| Test Case             | Concurrency | Max Output Tokens | Average Latency | P95 Latency | Approx Tokens/sec | Peak VRAM |
| --------------------- | ----------: | ----------------: | --------------: | ----------: | ----------------: | --------: |
| Basic generation      |           1 |               150 |             TBD |         TBD |               TBD |       TBD |
| Concurrent generation |           2 |               150 |             TBD |         TBD |               TBD |       TBD |
| Concurrent generation |           4 |               150 |             TBD |         TBD |               TBD |       TBD |
| Concurrent generation |           8 |               150 |             TBD |         TBD |               TBD |       TBD |

---

## Trade-Offs

### Why vLLM

vLLM was selected because it provides production-style LLM serving with OpenAI-compatible APIs, efficient GPU memory usage, continuous batching, streaming support, and native operational endpoints such as health and metrics.

### Why Qwen2.5-7B-Instruct

A 7B model is a practical balance for a 24GB GPU. It is large enough to produce useful instruction-following responses but small enough to deploy without multi-GPU infrastructure.

### Why `--max-model-len 4096`

The context length was limited to 4096 to keep VRAM usage stable on a 24GB GPU. Larger context windows increase KV-cache memory pressure and may reduce concurrency or increase p95 latency.

---

## Limitations

Current limitations:

* Docker Compose was not fully validated due to Docker daemon limitations.
* External Postman access depends on provider port exposure.
* No production reverse proxy yet.
* No HTTPS yet.
* No full Grafana dashboard yet.
* API key is static for test purposes.
* Benchmark table should be filled with final measured numbers.

---

## Final Status

| Requirement                        | Status                                         |
| ---------------------------------- | ---------------------------------------------- |
| Open-source LLM selected           | Completed                                      |
| vLLM serving                       | Completed                                      |
| OpenAI-compatible API              | Completed                                      |
| API-key authentication             | Completed                                      |
| Health check endpoint              | Completed                                      |
| Streaming support                  | Completed                                      |
| Local API test                     | Completed                                      |
| Load test script                   | Prepared                                       |
| External Postman test              | Depends on provider port exposure / SSH tunnel |
| Docker Compose                     | Pending GPU VM with Docker daemon              |
| Runtime troubleshooting documented | Completed                                      |
