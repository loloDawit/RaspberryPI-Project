from flask import Flask,request,render_template
import sys
import Adafruit_DHT
import sqlite3
import datetime 
import time
import json
import arrow 
import plotly.plotly as py
from plotly.graph_objs import *
import json
import urllib
import pyrebase

config = {
    "apiKey": "AIzaSyCjus5r37Db4dTxNjUzAI_hzsRj-Y_MGXk",
    "authDomain": "raspberrypi-6291e.firebaseapp.com",
    "databaseURL": "https://raspberrypi-6291e.firebaseio.com",
    "projectId": "raspberrypi-6291e",
    "storageBucket": "raspberrypi-6291e.appspot.com",
    "messagingSenderId": "199006368775"
  }
firebase = pyrebase.initialize_app(config)
db = firebase.database()

app = Flask(__name__)
app.debug = True

@app.route("/")
def hello():
    return render_template("home.html")

@app.route("/signin")
def login():
    return render_template("signin.html")
@app.route("/home_temp")
def home_temp():
    humidity,temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
    if humidity is not None and temperature is not None:
        return render_template("home_temp.html",temp=temperature,hum=humidity)
    else:
        return render_template("no_sensor.html")

@app.route("/home_env_db", methods=['GET'])
def home_env_db():
    temperatures, humidities, timezone, from_date_str, to_date_str = getDataRecords()

    #Create new record tables so the datetime are adjusted
    time_adjusted_temperatures = []
    time_adjusted_humidities  = []

    for record in temperatures:
        local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
        time_adjusted_temperatures.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])
    for record in humidities:
        local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
        time_adjusted_humidities.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])  

    print("Rendering current html with : %s, %s, %s" % (timezone, from_date_str,to_date_str))

    return render_template("home_env_db.html",timezone= timezone, temp=time_adjusted_temperatures,hum=time_adjusted_humidities,from_date=from_date_str,to_date = to_date_str)

@app.route("/data.json")
def getTemJsonData():
    db_connect    = sqlite3.connect('/var/www/lab_app/home_app.db') #provide an absolute file path
                                                                     #to the database 
    curs = db_connect.cursor()
    curs.execute("SELECT *FROM temperatures");
    temperatures = curs.fetchall()
    return json.dumps(temperatures); 
@app.route("/graph")
def graphTemp():
    return render_template('graph.html')
@app.route("/humdata.json")
def getHumJsonData():
    db_connect    = sqlite3.connect('/var/www/lab_app/home_app.db') #provide an absolute file path
                                                                     #to the database 
    curs = db_connect.cursor()
    curs.execute("SELECT *FROM humidities");
    humidity = curs.fetchall()
    return json.dumps(humidity); 

def getDataRecords(): 
    from_date_str = request.args.get('from',time.strftime("%Y-%m-%d 00:00")) #get the from_date
    to_date_str   = request.args.get('to',time.strftime("%Y-%m-%d %H:%M")) #get the to_date
    range_h_form  = request.args.get('range_h','')   #returns a string 
    timezone      = request.args.get('timezone', 'Etc/UTC');
    print(from_date_str) #testing the url date
    print(to_date_str)

    range_h_int  = "none" #initalise this variable with a string 

    try:
        range_h_int   = int(range_h_form) # convert the string to ints
    except:
        print ("Data in range_h_from not a number")

    if not validate_Date(from_date_str):
        from_date_str = time.strftime("%Y-%m-%d 00:00")

    if not validate_Date(to_date_str):
        to_date_str   =  time.strftime("%Y-%m-%d %H:%M")  
    #create datetime object so that we can covert to UTC from the browers local time 
    from_date_obj     = datetime.datetime.strptime(from_date_str,'%Y-%m-%d %H:%M')
    to_date_obj       = datetime.datetime.strptime(to_date_str,'%Y-%m-%d %H:%M')
    #if we radio button is clicked 
    if isinstance(range_h_int,int):
        arrow_time_from     = arrow.utcnow().replace(hours =-range_h_int)
        arrow_time_to       = arrow.utcnow()
        from_date_utc       = arrow_time_from.strftime("%Y-%m-%d %H:%M")
        to_date_utc         = arrow_time_to.strftime("%Y-%m-%d %H:%M")
        from_date_str       = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
        to_date_str         = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
    else:
        #convert datetimes to UTC so we can retrive the approprite records from the database
        from_date_utc = arrow.get(from_date_obj,timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")
        to_date_utc = arrow.get(to_date_obj,timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")

    db_connect    = sqlite3.connect('/var/www/lab_app/home_app.db') #provide an absolute file path
                                                                     #to the database 
    curs = db_connect.cursor()
    curs.execute("SELECT *FROM temperatures WHERE rDatatime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
    temperatures = curs.fetchall()
    curs.execute("SELECT *FROM humidities WHERE rDatatime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
    humidities = curs.fetchall()
    db_connect.close()
    return [temperatures,humidities, timezone, from_date_str,to_date_str]
@app.route("/to_plotly", methods=['GET'])
def to_plotly():
    temperatures, humidities, timezone, from_date_str, to_date_str = getDataRecords()

    #create new record
    time_series_adjusted_tempreratures  = []
    time_series_adjusted_humidities 	= []
    time_series_temprerature_values 	= []
    time_series_humidity_values 		= []

    for record in temperatures:
        local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
        time_series_adjusted_tempreratures.append(local_timedate.format('YYYY-MM-DD HH:mm'))
        time_series_temprerature_values.append(round(record[2],2))
    
    for record in humidities:
        local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
        time_series_adjusted_humidities.append(local_timedate.format('YYYY-MM-DD HH:mm')) #Best to pass datetime in text 
        #so that Plotly respects it
        time_series_humidity_values.append(round(record[2],2))
    temp = Scatter(
        		x=time_series_adjusted_tempreratures,
        		y=time_series_temprerature_values,
        		name='Temperature'
    				)
    hum = Scatter(
        		x=time_series_adjusted_humidities,
        		y=time_series_humidity_values,
        		name='Humidity',
        		yaxis='y2'
    				)
    data = Data([temp, hum])
    layout = Layout(
					title="Temperature and humidity inside my Home",
				    xaxis=XAxis(
				        type='date',
				        autorange=True
				    ),
				    yaxis=YAxis(
				    	title='Celcius',
				        type='linear',
				        autorange=True
				    ),
				    yaxis2=YAxis(
				    	title='Percent',
				        type='linear',
				        autorange=True,
				        overlaying='y',
				        side='right'
				    )

					)
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='home_temp_hum')
    return plot_url

def validate_Date(date):
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False
@app.route('/firebase')
def sendData():
    #authenticate a user
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password("william@hackbrightacademy.com", "mySuperStrongPassword")
    
    db_connect    = sqlite3.connect('/var/www/lab_app/home_app.db') #provide an absolute file path
                                                                     #to the database 
    curs = db_connect.cursor()
    curs.execute("SELECT *FROM humidities");
    humidity = curs.fetchall()
    curs.execute("SELECT *FROM temperatures");
    temperature = curs.fetchall()


    db.child("tempRecord").push(temperature)
    db.child("humRecord").push(humidity)

    return 'Success'
def getFirebaseData():
    getdata = db.child("tempRecord").get()
    
    for data in getdata.each():
        print (data.key())
        print (data.val()) 
    return 'Hey'  

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080)
    
