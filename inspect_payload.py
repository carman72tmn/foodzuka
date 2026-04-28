import json
import sys

def main():
    try:
        with open('/tmp/payload_735.json', 'r') as f:
            data = json.load(f)
        
        order = data.get('eventInfo', {}).get('order', {})
        print("--- FULL ORDER DATA ---")
        print(json.dumps(order, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
