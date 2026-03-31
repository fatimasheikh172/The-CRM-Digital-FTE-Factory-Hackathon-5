"""
TechCorp Customer Success AI Agent - Async Load Tests

Alternative load test using aiohttp (does not need locust installed).
Can be run standalone or integrated with pytest.
"""

import asyncio
import aiohttp
import time
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime


# ============================================================================
# ASYNC LOAD TEST FUNCTIONS
# ============================================================================

async def run_concurrent_requests(
    session: aiohttp.ClientSession,
    url: str,
    method: str,
    json_data: Optional[Dict] = None,
    count: int = 100,
    concurrent: int = 10
) -> Dict[str, Any]:
    """
    Send multiple requests with concurrent connections.
    
    Args:
        session: aiohttp ClientSession.
        url: Target URL.
        method: HTTP method (GET/POST).
        json_data: JSON body for POST requests.
        count: Total number of requests to send.
        concurrent: Number of concurrent connections.
        
    Returns:
        Dictionary with results:
        {
            "total": count,
            "success": N,
            "failed": N,
            "avg_ms": float,
            "p95_ms": float,
            "p99_ms": float,
            "rps": float
        }
    """
    results = []
    success_count = 0
    failed_count = 0
    
    async def make_request():
        nonlocal success_count, failed_count
        start = time.time()
        try:
            if method.upper() == "POST":
                async with session.post(url, json=json_data) as response:
                    elapsed = (time.time() - start) * 1000
                    if response.status == 200:
                        success_count += 1
                    else:
                        failed_count += 1
                    results.append(elapsed)
            else:
                async with session.get(url) as response:
                    elapsed = (time.time() - start) * 1000
                    if response.status == 200:
                        success_count += 1
                    else:
                        failed_count += 1
                    results.append(elapsed)
        except Exception as e:
            failed_count += 1
            elapsed = (time.time() - start) * 1000
            results.append(elapsed)
    
    # Run requests with concurrency limit
    semaphore = asyncio.Semaphore(concurrent)
    
    async def limited_request():
        async with semaphore:
            await make_request()
    
    start_time = time.time()
    tasks = [limited_request() for _ in range(count)]
    await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    # Calculate statistics
    if results:
        avg_ms = statistics.mean(results)
        sorted_results = sorted(results)
        p95_idx = int(len(sorted_results) * 0.95)
        p99_idx = int(len(sorted_results) * 0.99)
        p95_ms = sorted_results[p95_idx] if p95_idx < len(sorted_results) else sorted_results[-1]
        p99_ms = sorted_results[p99_idx] if p99_idx < len(sorted_results) else sorted_results[-1]
    else:
        avg_ms = p95_ms = p99_ms = 0
    
    rps = count / total_time if total_time > 0 else 0
    
    return {
        "total": count,
        "success": success_count,
        "failed": failed_count,
        "avg_ms": round(avg_ms, 2),
        "p95_ms": round(p95_ms, 2),
        "p99_ms": round(p99_ms, 2),
        "rps": round(rps, 2),
        "duration_sec": round(total_time, 2)
    }


async def load_test_all_endpoints(base_url: str = "http://localhost:8000") -> Dict[str, Dict]:
    """
    Test all major endpoints with load.
    
    Tests:
    - POST /support/submit (100 requests, 10 concurrent)
    - POST /webhooks/gmail/test (50 requests, 5 concurrent)
    - POST /webhooks/whatsapp/test (50 requests, 5 concurrent)
    - GET /health (200 requests, 20 concurrent)
    - GET /metrics/summary (100 requests, 10 concurrent)
    
    Returns:
        Results for all endpoints.
    """
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Web form submissions
        print("Testing POST /support/submit (100 requests, 10 concurrent)...")
        form_data = {
            "name": "Load Test User",
            "email": "loadtest@test.com",
            "subject": "Load Test Subject",
            "category": "General",
            "priority": "medium",
            "message": "This is a load test message."
        }
        results["web_form"] = await run_concurrent_requests(
            session, f"{base_url}/support/submit", "POST",
            json_data=form_data, count=100, concurrent=10
        )
        
        # Test 2: Email webhooks
        print("Testing POST /webhooks/gmail/test (50 requests, 5 concurrent)...")
        email_data = {
            "from_email": "test@test.com",
            "subject": "Load Test",
            "body": "Load test message"
        }
        results["email_webhook"] = await run_concurrent_requests(
            session, f"{base_url}/webhooks/gmail/test", "POST",
            json_data=email_data, count=50, concurrent=5
        )
        
        # Test 3: WhatsApp webhooks
        print("Testing POST /webhooks/whatsapp/test (50 requests, 5 concurrent)...")
        whatsapp_data = {
            "from_phone": "+14155551234",
            "body": "load test"
        }
        results["whatsapp_webhook"] = await run_concurrent_requests(
            session, f"{base_url}/webhooks/whatsapp/test", "POST",
            json_data=whatsapp_data, count=50, concurrent=5
        )
        
        # Test 4: Health checks
        print("Testing GET /health (200 requests, 20 concurrent)...")
        results["health_check"] = await run_concurrent_requests(
            session, f"{base_url}/health", "GET",
            count=200, concurrent=20
        )
        
        # Test 5: Metrics
        print("Testing GET /metrics/summary (100 requests, 10 concurrent)...")
        results["metrics"] = await run_concurrent_requests(
            session, f"{base_url}/metrics/summary", "GET",
            count=100, concurrent=10
        )
    
    return results


async def run_24hour_simulation(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Simulate 24 hours of traffic in fast forward.
    
    Simulates:
    - 100+ web form submissions
    - 50+ email messages
    - 50+ WhatsApp messages
    - 10+ customers using multiple channels
    
    Returns:
        Simulation results with metrics.
    """
    print("Starting 24-hour traffic simulation (fast forward)...")
    print("=" * 60)
    
    start_time = time.time()
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    response_times = []
    
    async with aiohttp.ClientSession() as session:
        # Simulate traffic bursts
        for hour in range(24):
            print(f"  Simulating hour {hour + 1}/24...")
            
            # Web form submissions (4-5 per hour average = 100+/day)
            for _ in range(5):
                total_requests += 1
                start = time.time()
                try:
                    form_data = {
                        "name": f"Hour {hour} User",
                        "email": f"hour{hour}@test.com",
                        "subject": "Test",
                        "category": "General",
                        "priority": "medium",
                        "message": "Test message"
                    }
                    async with session.post(f"{base_url}/support/submit", json=form_data) as resp:
                        elapsed = (time.time() - start) * 1000
                        response_times.append(elapsed)
                        if resp.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                except:
                    failed_requests += 1
            
            # Email messages (2 per hour = 50+/day)
            for _ in range(2):
                total_requests += 1
                start = time.time()
                try:
                    email_data = {
                        "from_email": f"hour{hour}@test.com",
                        "subject": "Test",
                        "body": "Test"
                    }
                    async with session.post(f"{base_url}/webhooks/gmail/test", json=email_data) as resp:
                        elapsed = (time.time() - start) * 1000
                        response_times.append(elapsed)
                        if resp.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                except:
                    failed_requests += 1
            
            # WhatsApp messages (2 per hour = 50+/day)
            for _ in range(2):
                total_requests += 1
                start = time.time()
                try:
                    whatsapp_data = {
                        "from_phone": "+14155551234",
                        "body": "test"
                    }
                    async with session.post(f"{base_url}/webhooks/whatsapp/test", json=whatsapp_data) as resp:
                        elapsed = (time.time() - start) * 1000
                        response_times.append(elapsed)
                        if resp.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                except:
                    failed_requests += 1
            
            # Small delay to simulate time passing
            await asyncio.sleep(0.1)
    
    total_time = time.time() - start_time
    
    # Calculate metrics
    uptime = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
    avg_response = statistics.mean(response_times) if response_times else 0
    sorted_times = sorted(response_times)
    p95_response = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
    
    return {
        "total_requests": total_requests,
        "successful": successful_requests,
        "failed": failed_requests,
        "uptime_percent": round(uptime, 2),
        "error_rate_percent": round(error_rate, 2),
        "avg_response_ms": round(avg_response, 2),
        "p95_response_ms": round(p95_response, 2),
        "duration_sec": round(total_time, 2),
        "requests_per_sec": round(total_requests / total_time, 2) if total_time > 0 else 0
    }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run all async load tests."""
    print("=" * 70)
    print("TechCorp Customer Success FTE - Async Load Tests")
    print("=" * 70)
    print("")
    
    base_url = "http://localhost:8000"
    
    # Test all endpoints
    print("Running endpoint load tests...")
    print("")
    results = await load_test_all_endpoints(base_url)
    
    print("")
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    for endpoint, data in results.items():
        print(f"\n{endpoint.upper()}:")
        print(f"  Total: {data['total']}, Success: {data['success']}, Failed: {data['failed']}")
        print(f"  Avg: {data['avg_ms']}ms, P95: {data['p95_ms']}ms, P99: {data['p99_ms']}ms")
        print(f"  RPS: {data['rps']}")
    
    print("")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
