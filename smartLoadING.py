import requests
import time
import datetime
import matplotlib.pyplot as plt

r = requests.get('https://api.awattar.de/v1/marketdata')
data = r.json()['data']
hours = []
prices = []
for point in data :
    prices.append(point['marketprice'])
    print(point['marketprice'])
    hours.append(datetime.datetime.fromtimestamp(point['start_timestamp']/1000).strftime('%H'))
    print(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
print(time.time())
print(int(time.time()*1e6))
plt.plot(hours, prices)
plt.show()