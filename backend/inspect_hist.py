import inspect
from pymax.client_web import WebClient

client = WebClient(session_name="test_hist.db")
print("fetch_history source:")
try:
    print(inspect.getsource(client.fetch_history))
except Exception as e:
    print("Error:", e)
