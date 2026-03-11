import requests
import time

def test_rate_limiting():
    print("Rate Limiting Test")
    print("-"*30)

    url = "http://127.0.0.1:5000/mistralai"

    print("\n1. Checking if server is running")
    try:
        response = requests.get(url, timeout=5)
        print(f"   Server responded with status: {response.status_code}")
    except:
        print("   ERROR: Server is not running")
        print("   Start it with: python app.py")
        return

    print("\n2. Testing rate limit (10 requests/minute on /news endpoints)")
    print("   Making 12 rapid requests to /mistralai page")

    status_codes = []
    for i in range(12):
        try:
            response = requests.get(url, timeout=5)
            status_codes.append(response.status_code)
            print(f"   Request {i+1:2d}: Status {response.status_code}")
        except Exception as e:
            print(f"   Request {i+1:2d}: ERROR - {e}")
            status_codes.append(0)

    print("\n3. Results:")
    if 429 in status_codes:
        first_429 = status_codes.index(429) + 1
        print(f"   Rate limiting is working")
        print(f"   Got 429 (Too Many Requests) on request #{first_429}")
    else:
        print(f"   All requests completed")
        print(f"   Status codes: {set(status_codes)}")
        print("   Note: /mistralai page may not be rate-limited")
        print("   Try testing /mistralai/news endpoint for stricter limits")

    print("\n" + "-"*30)
    print("Test Complete")

if __name__ == "__main__":
    test_rate_limiting()
