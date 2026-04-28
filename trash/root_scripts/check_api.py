import urllib.request
import json

def run():
    try:
        url = "http://localhost:8000/api/v1/orders/"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                data = json.loads(content)
                summary = []
                for o in data[:10]:
                    summary.append({
                        "id": o.get("id"),
                        "delivery_address": o.get("delivery_address"),
                        "order_type": o.get("order_type"),
                        "street": o.get("street"),
                        "house": o.get("house")
                    })
                print(json.dumps(summary, indent=2, ensure_ascii=False))
            else:
                print(f"Error status: {response.status}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    run()
