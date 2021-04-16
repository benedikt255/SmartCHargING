import requests

r = requests.get('https://api.awattar.de/v1/marketdata')
data = r.json()
print(data)