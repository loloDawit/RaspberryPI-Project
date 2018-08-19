import sqlite3
import sys
import Adafruit_DHT

def log_values(sensor_id,temp,hum):
    db_connect = sqlite3.connect('/var/www/lab_app/home_app.db') #provide an absolute file path
                                                                 #to the database 
    curs = db_connect.cursor()
    curs.execute("""INSERT INTO temperatures values(datetime(CURRENT_TIMESTAMP,'localtime'),(?),(?))""",(sensor_id,temp))
    curs.execute("""INSERT INTO humidities values(datetime(CURRENT_TIMESTAMP,'localtime'),(?),(?))""",(sensor_id,hum))
    db_connect.commit()
    db_connect.close()

humudity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302,17)

if humudity is not None and temperature is not None:
    log_values("1",temperature,humudity)
else:
    log_values("1",-888,-888)



