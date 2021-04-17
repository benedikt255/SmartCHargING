import requests
import time
import datetime
import matplotlib.pyplot as plt

hoursBeforeNow = 24
hoursFromNow = 24
startTime = int((time.time()- hoursBeforeNow*3600)*1e3)
endTime = int((time.time()+ hoursFromNow*3600)*1e3)
r = requests.get('https://api.awattar.de/v1/marketdata?start='+str(startTime)+'&end='+str(endTime))
data = r.json()['data']
hours = []
prices = []
for point in data :
    prices.append(point['marketprice']/1000+0.21) # + 21ct für Karlsruhe
    print(point['marketprice'])
    hours.append(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
    print(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
print(time.time())
print(int(time.time()*1e3))
plt.xlabel('hours')
plt.ylabel('price €/kWh')
plt.plot(hours, prices)
plt.gcf().autofmt_xdate()
plt.show()