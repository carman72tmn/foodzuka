import httpx
import time
from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine
from app.models.tbank_settings import TBankSettings
from app.core.tbank_utils import generate_tbank_qrpay_signature

with Session(engine) as db:
    settings = db.exec(select(TBankSettings)).first()

url = 'https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY'
keys_to_test = [
    ('settings.token', settings.token),
    ('settings.terminal_key', settings.terminal_key)
]
terminals_to_test = [
    ('terminal_delivery', settings.terminal_delivery.strip() if settings.terminal_delivery else None),
    ('terminal_pickup', settings.terminal_pickup.strip() if settings.terminal_pickup else None),
    ('mch_id_as_ter', '400000001164353')
]
mch_ids_to_test = ['400000001164353', ' 400000001164353']

for key_name, secret_key in keys_to_test:
    for term_name, ter_id in terminals_to_test:
        for mch_id in mch_ids_to_test:
            out_transaction_no = str(int(time.time() * 100))
            payload = {
                'mchId': mch_id.strip(),
                'terId': ter_id,
                'currency': '643',
                'totalAmount': '10.00',
                'outTransactionNo': out_transaction_no,
                'subject': 'Тест оплаты',
                'tradeType': 'pay.paxpay.native',
                'version': 'V1.0',
                'signType': 'HMAC_SHA256',
                'timeStart': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
            payload['signature'] = generate_tbank_qrpay_signature(payload, secret_key, 'qrpay')
            with httpx.Client(timeout=5.0, verify=False) as client:
                try:
                    res = client.post(url, json=payload)
                    data = res.json()
                    c = data.get('code')
                    m = data.get('msg')
                    print(key_name + ' | ' + term_name + ' (' + str(ter_id) + ') | Mch: [' + mch_id + '] -> Code: ' + str(c) + ', Msg: ' + str(m))
                    if c == 'SUCCESS':
                        print('  SUCCESS! URL: ' + str(data.get('codeUrl')))
                except Exception as e:
                    print('Err:', e)
            time.sleep(0.2)
