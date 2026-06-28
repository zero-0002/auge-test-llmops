import asyncio
import time
import statistics
import httpx

URL = "http://localhost:8080/v1/chat/completions"
API_KEY = "test-secret-key"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

CONCURRENCY = 2
REQUESTS = 10

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "Explain what a vector database is in 100 words."}
    ],
    "temperature": 0.2,
    "max_tokens": 150
}


async def send_request(client):
    start = time.time()
    response = await client.post(
        URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=120
    )
    latency = time.time() - start

    try:
        data = response.json()
        usage = data.get("usage", {})
        output_tokens = usage.get("completion_tokens", 0)
    except Exception:
        output_tokens = 0

    return {
        "status": response.status_code,
        "latency": latency,
        "output_tokens": output_tokens
    }


async def main():
    results = []

    async with httpx.AsyncClient() as client:
        for i in range(0, REQUESTS, CONCURRENCY):
            batch = [send_request(client) for _ in range(CONCURRENCY)]
            results.extend(await asyncio.gather(*batch))

    latencies = [r["latency"] for r in results]
    output_tokens = sum(r["output_tokens"] for r in results)
    total_time = sum(latencies)

    print("Requests:", len(results))
    print("Statuses:", [r["status"] for r in results])
    print("Average latency:", round(statistics.mean(latencies), 3), "s")
    print("P95 latency:", round(statistics.quantiles(latencies, n=20)[18], 3), "s")
    print("Total output tokens:", output_tokens)
    print("Approx tokens/sec:", round(output_tokens / total_time, 2) if total_time else 0)


if __name__ == "__main__":
    asyncio.run(main())
