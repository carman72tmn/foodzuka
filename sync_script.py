import urllib.request
import json
import sys

def trigger_post(url):
    print(f"Triggering POST {url}...")
    try:
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode()
            print(f"Response: {data}")
            return data
    except Exception as e:
        print(f"Error triggering {url}: {e}")
        return None

if __name__ == "__main__":
    base_url = "http://localhost:8000/api/v1/iiko"
    print("--- SYNC PAYMENT TYPES ---")
    trigger_post(f"{base_url}/sync-payment-types")
    
    # Try to call iiko_service directly via a temporary script if needed, 
    # but first let's see why the endpoint returns 0.
    # We can check the backend logs for 'DEBUG iiko request'
