import requests
import time
import datetime
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.messagebox as msg
from tkcalendar import Calendar, DateEntry
import math
import csv

priceOffset=0.21
solarEfficiency=0.85

def ggt(a, b):
    while b!=0:
        c=a%b
        a=b
        b=c
    return a

class Config:
    capacity=50 #in kWh
    startSoC=20 #in %
    endSoC=80 #in %
    chargePower=11 #in kW
    solarPeakPower=0 #in kW
    solarCost=0.08 #in ct/kWh
    startTime=datetime.datetime.fromtimestamp(time.time())
    endTime=datetime.datetime.fromtimestamp(time.time()+24*3600)

class Results:
    hours=[] # timestamp
    prices=[] # price of energy in €
    SoC=[] # SoC of the battery in %
    charging=[] # power with which is charged
    solarPower=[] # power produced by pv
    savings=0 # savings in €
    solarQuote=0 # % of charge contributed by solar

#efficiency: 100% ^= 1000W/m²
#eta*A=P --> Wh/kWP einfach
class SolarData:
    intervall=0
    power=[]

    def __init__(self, config=None):
        self.config = config

    def getData(self):
        self.power=[]
        with open('solar_short.csv', newline='') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                dt = datetime.datetime.fromisoformat(row[0])
                if dt >= self.config.startTime and dt <= self.config.endTime:
                    self.power.append([dt, 2.7e-3*float(row[1])])
        if len(self.power) > 0:
            self.intervall=self.power[1][0]-self.power[0][0]
        return self.power #kWh per intervall

    def findItem(self, time):
        i=0
        while i < len(self.power):
            if self.power[i][0] <= time and i+1<len(self.power) and self.power[i+1][0] > time:
                return self.power[i]
            i+=1
        return None

class MarketData:
    intervall=0
    data = []

    def __init__(self, config=None):
        self.config = config

    def getData(self):
        self.data = []
        startTime = int(self.config.startTime.timestamp()*1e3)
        endTime = int(self.config.endTime.timestamp()*1e3)
        r = requests.get('https://api.awattar.de/v1/marketdata?start='+str(startTime)+'&end='+str(endTime))
        self.data =r.json()['data']
        self.intervall=datetime.datetime.fromtimestamp(self.data[0]['end_timestamp']/1000)-datetime.datetime.fromtimestamp(self.data[0]['start_timestamp']/1000)
        return self.data    

    def findItem(self, time):
        for item in self.data:
            if datetime.datetime.fromtimestamp(item['start_timestamp']/1000) <= time and datetime.datetime.fromtimestamp(item['end_timestamp']/1000) > time:
                return item
        return None


class Calc:
    def __init__(self, config=None):
        self.config = config    

    def chargePeriod(self, SoC, period, price):
        SoCnew=min(self.config.endSoC, (period*self.config.chargePower)/self.config.capacity*100+SoC)
        cost=(SoCnew-SoC)*0.01*self.config.capacity*price
        return (SoCnew,cost)

    def charge(self):
        market = MarketData(config)
        priceData=market.getData()
        results=Results()
        solar = SolarData(config)
        power=solar.getData()
        #calculate power delivered py solar
        solarEnergy=0
        for energy in power:
            solarEnergy+=energy[1]*0.85*config.solarPeakPower if energy[1]*solarEfficiency*config.solarPeakPower/(solar.intervall.total_seconds()/3600) <= config.chargePower else config.chargePower * solar.intervall.total_seconds()/3600
        chargeEnergy=(config.endSoC-config.startSoC)*0.01*config.capacity
        cost=0
        costDumb=0
        SoCDumb=config.startSoC
        SoC=config.startSoC
        #use old algorythm when no solar power present
        #1. sort data pricewise
        #2. calculate charging time
        #3. take price of charging time/intervall_length element as threshold
        #4. charge in all intervalls cheaper than threshold
        if solarEnergy == 0:
            chargeTime=(config.endSoC-config.startSoC)*0.01*config.capacity/config.chargePower
            #sort data pricewise
            data = priceData
            elements=sorted(data,key=lambda point: point['marketprice'])
            threshold=elements[min(math.ceil(chargeTime),len(elements)-1)]['marketprice']
            i=0
            for point in data:
                price=point['marketprice']/1000+priceOffset
                period=float((datetime.datetime.fromtimestamp(point['end_timestamp']/1000)-datetime.datetime.fromtimestamp(point['start_timestamp']/1000)).seconds)/3600 #period in hours
                results.prices.append(point['marketprice']/1000+priceOffset)
                results.hours.append(datetime.datetime.fromtimestamp(point['start_timestamp']/1000))
                results.SoC.append(SoC)
                results.solarPower.append(0.85*power[i][1]*config.solarPeakPower/period if len(power) > i else 0)
                results.charging.append(self.config.chargePower if point['marketprice'] < threshold else 0)
                #calculate SoC and price
                if point['marketprice'] < threshold:
                    res=self.chargePeriod(SoC, period, price)
                    SoC=res[0]
                    cost+=res[1]
                res=self.chargePeriod(SoCDumb, period, price)
                SoCDumb=res[0]
                costDumb+=res[1]
                i+=1
            print(cost)
            print(costDumb)
            results.savings = round((costDumb - cost),2)
            results.solarQuote=0
        else:
        #A) if solar is enough, use only solar
        #B) 1. calculate missing energy
        #   2. sort timeslots pricewise
        #   3. calculate additional charging energy per timeslot till battery is full. limit to max charging power
        #if solar is not enough calculate data for each timeslot
            #sort data pricewise
            calcIntervall=datetime.timedelta(seconds=ggt(solar.intervall.total_seconds(),market.intervall.total_seconds()))
            priceData.sort(key=lambda point: point['marketprice'])
            calcTime=config.startTime
            pvIndex=0
            netEngergy=chargeEnergy-solarEnergy
            remainNetEnergy=netEngergy
            threshold=0
            for point in priceData:
                slotTime=datetime.datetime.fromtimestamp(point['start_timestamp']/1000)
                while slotTime<datetime.datetime.fromtimestamp(point['end_timestamp']/1000):
                    slotTime +=calcIntervall
                    solarPower=(solar.findItem(slotTime)[1] if solar.findItem(slotTime) != None else 0)*solarEfficiency*config.solarPeakPower/(solar.intervall.total_seconds()/3600)
                    remainNetEnergy-=(self.config.chargePower-solarPower)*calcIntervall.total_seconds()/3600
                if remainNetEnergy <0:
                    threshold=point['marketprice']/1000+priceOffset
                    break
            remainNetEnergy=netEngergy
            while calcTime < config.endTime:
                #pv data is sorted after time
                price=market.findItem(calcTime)['marketprice']/1000+priceOffset if market.findItem(calcTime) != None else 0
                deltaSolar=solar.findItem(calcTime)[1] if solar.findItem(calcTime) != None else 0
                maxPower=min(config.chargePower, (self.config.endSoC-SoC)/100*self.config.capacity/(calcIntervall.total_seconds()/3600))
                currPowerSolar=min(deltaSolar*solarEfficiency*config.solarPeakPower/(calcIntervall.total_seconds()/3600), maxPower)
                maxNetPower=min(maxPower-currPowerSolar, remainNetEnergy/(calcIntervall.total_seconds()/3600))
                currPowerNet= maxNetPower if (price > 0 and price<=threshold) else 0
                remainNetEnergy-=currPowerNet*(calcIntervall.total_seconds()/3600)
                results.prices.append(price)
                results.hours.append(calcTime)
                results.SoC.append(SoC)
                results.solarPower.append(solarEfficiency*solar.findItem(calcTime)[1]*config.solarPeakPower/(calcIntervall.total_seconds()/3600) if solar.findItem(calcTime) != None else 0)
                results.charging.append(currPowerSolar+currPowerNet)
                #calculate SoC and price
                SoC=min(self.config.endSoC, ((calcIntervall.total_seconds()/3600)*(currPowerNet+currPowerSolar)/self.config.capacity*100+SoC))
                cost+=(currPowerSolar*(calcIntervall.total_seconds()/3600)*config.solarCost)+(currPowerNet*(calcIntervall.total_seconds()/3600)*price)
                if (price>0):
                    res=self.chargePeriod(SoCDumb, calcIntervall.total_seconds()/3600, price)
                    SoCDumb=res[0]
                    costDumb+=res[1]
                calcTime+=calcIntervall
            results.savings = round((costDumb - cost),2)
            results.solarQuote=round(min(solarEnergy/chargeEnergy, 1),2)
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
        self.l7 = tk.Label(self, text ="solar peak power /kW")
        self.l7.grid(row=8, column=0, sticky='nw')
        temp = tk.DoubleVar(value=config.solarPeakPower)
        self.solarPeakPower=tk.Spinbox(self, from_=0, to=30,increment=0.5, width=3, textvariable=temp)
        self.solarPeakPower.grid(row=8, column=1)   
        self.l8 = tk.Label(self, text ="solar cost ct/kWh")
        self.l8.grid(row=9, column=0, sticky='nw')
        temp = tk.DoubleVar(value=config.solarCost*100)
        self.solarCost=tk.Spinbox(self, from_=1, to=30,increment=0.5, width=3, textvariable=temp)
        self.solarCost.grid(row=9, column=1)   
        self.quit = tk.Button(self, text="apply", command=self.quit_action)
        self.quit.grid(row=10)

    def quit_action(self):
        self.config.startTime= datetime.datetime.fromisoformat(isostring_from_calendar_hour_minute(self.calBegin.get_date(), self.hourBegin.get(), self.minuteBegin.get()))
        self.config.endTime= datetime.datetime.fromisoformat(isostring_from_calendar_hour_minute(self.calEnd.get_date(), self.hourEnd.get(), self.minuteEnd.get()))
        self.config.chargePower= float(self.chargePower.get())
        self.config.startSoC= float(self.startSoC.get())
        self.config.endSoC= float(self.endSoC.get())
        self.config.capacity= float(self.capacity.get())
        self.config.solarCost= float(self.solarCost.get())/100
        self.config.solarPeakPower= float(self.solarPeakPower.get())
        calc = Calc(config)
        results=calc.charge()
        msg.showinfo(title="Congratulations", message="You haved saved " + str(results.savings) + " €\nYour pv contributed "+ str(results.solarQuote*100)+" percent of your charge")
        fig, ax1 = plt.subplots()
        fig.subplots_adjust(right=0.75)
        ax1.set_xlabel('hours')
        ax1.set_ylabel('price €/kWh')
        ax1.plot(results.hours, results.prices)
        ax2 = ax1.twinx()
        ax2.set_ylabel('power in kW', color='red')
        ax2.plot(results.hours, results.solarPower, color='orange')
        ax2.plot(results.hours, results.charging, color='red')
        ax3 = ax1.twinx()
        ax3.spines.right.set_position(("axes", 1.2))
        ax3.set_ylabel('SoC in percent', color='green')
        ax3.plot(results.hours, results.SoC, color='green')
        fig.tight_layout()
        #plt.gcf().autofmt_xdate()
        plt.get_current_fig_manager().canvas.set_window_title("Results")
        plt.title("Market prices over your selected time frame")
        plt.show()
        plt.close()

config = Config()
# Excecute Tkinter
root = tk.Tk()
app = Application(master=root, config=config)
app.master.title("Savings Calculator")
app.mainloop()


    
#calculate charging time
#print(time.time())
#print(int(time.time()*1e3))
