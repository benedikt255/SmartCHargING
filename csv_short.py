import csv
import datetime

#cleans the solar radiation data of DWD of unneeded values for photovoltaic estimation and removes all values older than 2015

with open('solar_ori.csv', newline='') as f:
    reader = csv.reader(f, delimiter=';')
    with open('solar_short.csv', 'w') as s:
        writer = csv.writer(s)
        count=0
        for row in reader:
            if count > 0:
                date = datetime.datetime.fromisoformat(row[1][0:4]+'-'+row[1][4:6]+'-'+row[1][6:8]+' '+row[1][8:10]+':'+row[1][10:12])
                if date.year > 2015:
                    row[1]=date.isoformat()
                    row.pop(7) 
                    row.pop(6) 
                    row.pop(5)
                    row.pop(3)
                    row.pop(2)
                    row.pop(0)
                    writer.writerow(row)
            count+=1