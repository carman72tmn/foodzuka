import chardet
path = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\iiko_sync_service.py'
with open(path, 'rb') as f:
    rawdata = f.read(1000)
    result = chardet.detect(rawdata)
    print(result)
