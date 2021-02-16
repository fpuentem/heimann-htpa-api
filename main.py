# main.py

# Standard library imports
import time
import csv
from datetime import datetime

# Third party imports
from flask import Flask, render_template, Response, json

# Local application imports
from libs.htpa import *


app = Flask(__name__)

# Thermal camera driver
dev = HTPA(0x1A)

@app.route('/home')
def home():
    return "<h1>Thermal measure HTPA - Visiontech</h1>"

@app.route('/raw-data', methods=['GET'])
# 
def get_raw_data():
    fr = dev.get_frame()
    frame = fr.tolist()
    temp = 25.5 

    # time stamp 
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y %H:%M:%S")

    data = {"raw-data" : frame, "ts": date_time}
    
    response = app.response_class(
        response = json.dumps(data),
        status = 200,
        mimetype = 'application/json'
    )
    return response

@app.route('/temperature', methods=['GET'])
# 
def get_raw_temperature():
    temp, fr = dev.get_frame_temperature()
    frame = fr.tolist() 

    # time stamp 
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y %H:%M:%S")

    data = {"raw-temperature" : frame, "amb-temp" : temp,
            "ts": date_time}
    
    response = app.response_class(
        response = json.dumps(data),
        status = 200,
        mimetype = 'application/json'
    )
    return response

if __name__ == '__main__':
    # defining server ip address and port
    app.run(host='0.0.0.0',port='5050', debug=True)
