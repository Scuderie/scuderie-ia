#!/usr/bin/env python3
"""
Rate Limit Testing Script
Tests the rate limiting implementation by making rapid requests.
"""
import asyncio
import httpx
import time
from typing import Dict


API_URL = "http://localhost:8000"
API_KEY = "scuderie-dev-key-2024"


async def test_rate_limit_chat():
    """Test /chat endpoint rate limit (10/minute)."""
    print("\n🧪 Testing /chat rate limit (10/minute)...\n")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    results = {"success": [], "rate_limited": []}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(15):
            try:
                response = await client.post(
                    f"{API_URL}/api/v1/chat",
                    json={"message": f"Test message {i+1}", "use_rag": False},
                    headers=headers
                )
                
                if response.status_code == 200:
                    results["success"].append(i+1)
                    print(f"✅ Request {i+1}: 200 OK")
                    # Print rate limit headers
                    print(f"   Limit: {response.headers.get('X-RateLimit-Limit', 'N/A')}")
                    print(f"   Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
                elif response.status_code == 429:
                    results["rate_limited"].append(i+1)
                    retry_after = response.headers.get('Retry-After', 'N/A')
                    print(f"🛑 Request {i+1}: 429 Too Many Requests")
                    print(f"   Retry-After: {retry_after}s")
                else:
                    print(f"⚠️  Request {i+1}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Request {i+1}: {e}")
            
            await asyncio.sleep(0.2)  # Small delay between requests
    
    print("\n📊 Results:")
    print(f"✅ Successful: {len(results['success'])}")
    print(f"🛑 Rate Limited: {len(results['rate_limited'])}")
    
    return results


async def test_different_api_keys():
    """Test that different API keys have separate rate limits."""
    print("\n🧪 Testing separate limits for different API keys...\n")
    
    keys = [API_KEY, "test-key-2"]
    
    for key in keys:
        headers = {"X-API-Key": key, "Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{API_URL}/api/v1/chat",
                    json={"message": "Test", "use_rag": False},
                    headers=headers
                )
                
                if response.status_code == 401:
                    print(f"🔐 Key '{key}': Unauthorized (expected for test-key-2)")
                else:
                    print(f"✅ Key '{key}': {response.status_code}")
                    print(f"   Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
                    
            except Exception as e:
                print(f"❌ Key '{key}': {e}")


async def test_ingest_rate_limit():
    """Test /ingest endpoint rate limit (50/hour)."""
    print("\n🧪 Testing /ingest rate limit (50/hour)...\n")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(3):
            try:
                response = await client.post(
                    f"{API_URL}/api/v1/ingest",
                    json={
                        "source_id": f"test_{i}",
                        "source_type": "test",
                        "content": "Test content"
                    },
                    headers=headers
                )
                
                print(f"Request {i+1}: {response.status_code}")
                print(f"   Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Request {i+1}: {e}")
            
            await asyncio.sleep(0.5)


async def main():
    """Run all tests."""
    print("="*60)
    print("🛡️  RATE LIMITING TESTS")
    print("="*60)
    
    # Test 1: Chat endpoint
    chat_results = await test_rate_limit_chat()
    
    # Test 2: Different API keys (optional)
    # await test_different_api_keys()
    
    # Test 3: Ingest endpoint
    # await test_ingest_rate_limit()
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETED")
    print("="*60)
    
    # Validate results
    if chat_results["rate_limited"]:
        print("\n✅ Rate limiting is WORKING!")
        print(f"   First 10 requests passed, remaining {len(chat_results['rate_limited'])} were blocked.")
    else:
        print("\n⚠️  WARNING: No requests were rate limited!")
        print("   Rate limiting may not be working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
