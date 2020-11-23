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
    return "<h1>People detection - Poli-USP</h1>"



if __name__ == '__main__':
    # defining server ip address and port
    app.run(host='0.0.0.0',port='5000', debug=True)
