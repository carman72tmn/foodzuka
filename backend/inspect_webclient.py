import inspect
from pymax.client_web import WebClient

print('init signature:', inspect.signature(WebClient.__init__))
print('start signature:', inspect.signature(WebClient.start))
print('connect signature:', inspect.signature(WebClient.connect))
