from flask import Flask 
from flask import request

import requests

app = Flask(__name__)

def get_country(ip_address):
    try:
        response = requests.get("http://ip-api.com/json/{}".format(ip_address))
        js = response.json()
        country = js['countryCode']
        return country
    except Exception as e:
        return "Unknown"

@app.route("/")
def home():
    ip_address = request.remote_addr
    country = get_country(ip_address)
    # number of countries where the largest number of speakers are French
    # data from http://download.geonames.org/export/dump/countryInfo.txt
    if country in ('BL', 'MF', 'TF', 'BF', 'BI', 'BJ', 'CD', 'CF', 'CG', 'CI', 'DJ', 'FR', 'GA', 'GF', 'GN', 'GP', 'MC', 'MG', 'ML', 'MQ', 'NC'):
        return "Bonjour"
    return f'Hello {ip_address}, {country}'

if __name__ == "__main__":
    app.run()
