import chardet
with open('backend/app/services/iiko_sync_service.py', 'rb') as f:
    rawdata = f.read(10000)
    result = chardet.detect(rawdata)
    print(result)
