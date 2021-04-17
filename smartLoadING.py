import requests
import time
import datetime
import matplotlib.pyplot as plt

startTime = int(time.time()*1e3)
endTime = int((time.time()+ 24*3600)*1e3)
r = requests.get('https://api.awattar.de/v1/marketdata?start='+str(startTime)+'&end='+str(endTime))
data = r.json()['data']
hours = []
prices = []
for point in data :
    prices.append(point['marketprice']/1000+0.17)
    print(point['marketprice'])
    hours.append(datetime.datetime.fromtimestamp(point['start_timestamp']/1000).strftime('%H'))
    print(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
print(time.time())
print(int(time.time()*1e6))
plt.xlabel('hours')
plt.ylabel('price €/kWh')
plt.plot(hours, prices)
plt.show()