import requests
import time
import datetime
import matplotlib.pyplot as plt
import tkinter as tk 
from tkcalendar import Calendar, DateEntry
import math

class Config:
    capacity=50
    startSoC=20
    endSoC=80
    chargePower=2 #in kW
    startTime=datetime.datetime.fromtimestamp(time.time())
    endTime=datetime.datetime.fromtimestamp(time.time()+24*3600)

class Results:
    hours=[]
    prices=[]
    SoC=[]



def charge(config, SoC, period):
    SoCnew=min(config.endSoC, (period*config.chargePower)/config.capacity*100+SoC)
    price=(SoCnew-SoC)*0.01

class Calc:

    def __init__(self, config=None):
        self.config = config

    def getData(self):
        startTime = int(self.config.startTime.timestamp()*1e3)
        endTime = int(self.config.endTime.timestamp()*1e3)
        r = requests.get('https://api.awattar.de/v1/marketdata?start='+str(startTime)+'&end='+str(endTime))
        return r.json()['data']
    def charge(self):
        results=Results()
        chargeTime=(config.endSoC-config.startSoC)*0.01*config.capacity/config.chargePower
        #sort data pricewise
        elements=sorted(data,key=lambda point: point['marketprice'])
        threshold=elements[min(math.ceil(chargeTime),len(elements)-1)]
        chargePrice=0;
        chargePriceDumb=0;
        SoCDumb=config.startSoC;
        SoC=config.startSoC;

        for point in data :
            results.prices.append(point['marketprice']/1000+0.21) # + 21ct für Karlsruhe und Umrchnung von €/MWh zu 
            results.hours.append(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
            results.SoC=SoC
            #calculate SoC and price
            period=float((datetime.datetime.fromtimestamp(point['end_timestamp']/1000)-datetime.datetime.fromtimestamp(point['start_timestamp']/1000)).seconds)/3600 #period in hours
            SoC=min(config.endSoC, (period*config.chargePower)/config.capacity*100+SoC)
            SoCDumb=min(config.endSoC, (period*config.chargePower)/config.capacity*100+SoC)
        return results

def isostring_from_calendar_hour_minute(date, hour, minute):
    items = date.split(".")
    return '20'+items[2]+'-'+items[1]+'-'+items[0]+' '+format(float(hour), '02.0f')+':'+format(float(minute), '02.0f')

class Application(tk.Frame):
    def __init__(self, master=None, config=None):
        super().__init__(master)
        self.master = master
        self.config = config
        self.grid()
        self.create_widgets()

    def create_widgets(self):
        ## Add Calender
        self.l1 = tk.Label(self, text="Start")
        self.l1.grid(row=0, column=0, sticky='nw')
        self.calBegin = Calendar(self, selectmode = 'day', day = self.config.startTime.day, month = self.config.startTime.month, year = self.config.startTime.year)        
        self.calBegin.grid(row=1, column=1)
        temp = tk.DoubleVar(value=self.config.startTime.hour)
        self.hourBegin=tk.Spinbox(self, from_=0, to=23,increment=1, width=2, textvariable=temp)
        self.hourBegin.grid(row=1, column=2)
        temp = tk.DoubleVar(value=(int(self.config.startTime.minute/15)*15))
        self.minuteBegin=tk.Spinbox(self, from_=0, to=45,increment=15, width=2, textvariable=temp)
        self.minuteBegin.grid(row=1, column=3)
        self.l2 = tk.Label(self, text ="Ende")
        self.l2.grid(row=2, column=0, sticky='nw')
        self.calEnd = Calendar(self, selectmode = 'day', day = self.config.endTime.day, month = self.config.endTime.month, year = self.config.endTime.year)        
        self.calEnd.grid(row=3, column=1)
        temp = tk.DoubleVar(value=7)
        self.hourEnd=tk.Spinbox(self, from_=0, to=23,increment=1, width=2, textvariable=temp)
        self.hourEnd.grid(row=3, column=2)
        temp = tk.DoubleVar(value=30)
        self.minuteEnd=tk.Spinbox(self, from_=0, to=45,increment=15, width=2, textvariable=temp)
        self.minuteEnd.grid(row=3, column=3)   
        self.l3 = tk.Label(self, text ="StartSoC /%")
        self.l3.grid(row=4, column=0, sticky='nw')
        temp = tk.DoubleVar(value=config.startSoC)
        self.startSoC=tk.Spinbox(self, from_=0, to=100,increment=1, width=3, textvariable=temp)
        self.startSoC.grid(row=4, column=1)
        self.l4 = tk.Label(self, text ="EndSoC /%")
        self.l4.grid(row=5, column=0, sticky='nw')
        temp = tk.DoubleVar(value=config.endSoC)
        self.endSoC=tk.Spinbox(self, from_=0, to=100,increment=1, width=3, textvariable=temp)
        self.endSoC.grid(row=5, column=1)   
        self.l5 = tk.Label(self, text ="Charging power /kW")
        self.l5.grid(row=6, column=0, sticky='nw')
        temp = tk.DoubleVar(value=config.chargePower)
        self.chargePower=tk.Spinbox(self, from_=1, to=22,increment=1, width=3, textvariable=temp)
        self.chargePower.grid(row=6, column=1)   
        self.l6 = tk.Label(self, text ="capacity /kWh")
        self.l6.grid(row=7, column=0, sticky='nw')
        temp = tk.DoubleVar(value=config.capacity)
        self.capacity=tk.Spinbox(self, from_=1, to=130,increment=1, width=3, textvariable=temp)
        self.capacity.grid(row=7, column=1)   
        self.quit = tk.Button(self, text="apply", command=self.quit_action)
        self.quit.grid(row=8)

    def quit_action(self):
        self.config.startTime= datetime.datetime.fromisoformat(isostring_from_calendar_hour_minute(self.calBegin.get_date(), self.hourBegin.get(), self.minuteBegin.get()))
        self.config.endTime= datetime.datetime.fromisoformat(isostring_from_calendar_hour_minute(self.calEnd.get_date(), self.hourEnd.get(), self.minuteEnd.get()))
        self.config.chargePower= float(self.chargePower.get())
        self.config.startSoC= float(self.startSoC.get())
        self.config.endSoC= float(self.endSoC.get())
        self.config.capacity= float(self.capacity.get())
        self.master.destroy()

config = Config()
# Excecute Tkinter
root = tk.Tk()
app = Application(master=root, config=config)
app.master.title("config")
app.mainloop()


calc = Calc(config)
data = calc.getData()
results=calc.charge()
    
#calculate charging time
#print(time.time())
#print(int(time.time()*1e3))

def only_hours():
    only_hours = []
    for i in range(len(results.hours)):
        only_hours.append(results.hours[i].hour)

plt.xlabel('hours')
plt.ylabel('price €/kWh')
plt.plot(results.hours, results.prices)
plt.gcf().autofmt_xdate()
plt.show()