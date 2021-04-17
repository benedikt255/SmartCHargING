import requests
import time
import datetime
import matplotlib.pyplot as plt
import tkinter as tk 
from tkcalendar import Calendar, DateEntry

class Config:
    startTime=datetime.datetime.fromtimestamp(time.time())
    endTime=datetime.datetime.fromtimestamp(time.time()+24*3600)

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
        self.l1 = tk.Label(text="Start")
        self.l1.grid(row=0)
        self.calBegin = Calendar(self, selectmode = 'day', day = self.config.startTime.day, month = self.config.startTime.month, year = self.config.startTime.year)        
        self.calBegin.grid(row=1)
        temp = tk.DoubleVar(value=self.config.startTime.hour)
        self.hourBegin=tk.Spinbox(self, from_=0, to=23,increment=1, width=2, textvariable=temp)
        self.hourBegin.grid(row=2, column=0)
        temp = tk.DoubleVar(value=(int(self.config.startTime.minute/15)*15))
        self.minuteBegin=tk.Spinbox(self, from_=0, to=45,increment=15, width=2, textvariable=temp)
        self.minuteBegin.grid(row=2, column=1)
        self.l2 = tk.Label(text ="Ende")
        self.l2.grid(row=3)
        self.calEnd = Calendar(self, selectmode = 'day', day = self.config.endTime.day, month = self.config.endTime.month, year = self.config.endTime.year)        
        self.calEnd.grid(row=4)
        temp = tk.DoubleVar(value=7)
        self.hourEnd=tk.Spinbox(self, from_=0, to=23,increment=1, width=2, textvariable=temp)
        self.hourEnd.grid(row=5, column=0)
        temp = tk.DoubleVar(value=30)
        self.minuteEnd=tk.Spinbox(self, from_=0, to=45,increment=15, width=2, textvariable=temp)
        self.minuteEnd.grid(row=5, column=1)   
        self.quit = tk.Button(self, text="apply", command=self.quit_action)
        self.quit.grid(row=6)

    def quit_action(self):
        self.config.startTime= datetime.datetime.fromisoformat(isostring_from_calendar_hour_minute(self.calBegin.get_date(), self.hourBegin.get(), self.minuteBegin.get()))
        self.config.endTime= datetime.datetime.fromisoformat(isostring_from_calendar_hour_minute(self.calEnd.get_date(), self.hourEnd.get(), self.minuteEnd.get()))
        self.master.destroy()

config = Config()
# Excecute Tkinter
root = tk.Tk()
app = Application(master=root, config=config)
app.master.title("config")
app.mainloop()


print(config.startTime)
print(config.endTime)

data = []
startTime = int(config.startTime.timestamp()*1e3)
endTime = int(config.endTime.timestamp()*1e3)
r = requests.get('https://api.awattar.de/v1/marketdata?start='+str(startTime)+'&end='+str(endTime))
data = r.json()['data']
hours = []
prices = []
for point in data :
    prices.append(point['marketprice']/1000+0.21) # + 21ct für Karlsruhe und Umrchnung von €/MWh zu 
    #print(point['marketprice'])
    hours.append(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
    #print(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
#print(time.time())
#print(int(time.time()*1e3))
plt.xlabel('hours')
plt.ylabel('price €/kWh')
plt.plot(hours, prices)
plt.show()