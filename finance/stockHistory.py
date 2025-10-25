# This code uses the yfinance module to pull statistics instead of IEX cloud.
# Date: 06/28/2020
import yfinance as yf
import pandas as pd
import xlsxwriter
import time
import os
import numpy as np
from openpyxl import load_workbook
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Change to current working directory to pull files from same directory as script.
cwd = os.getcwd()
os.chdir(cwd)

# Authorize api scopes based on creds file.
def AuthorizeApi():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    return client

tickers = [
            'MSFT',
            'AAPL',
            'AMZN',
            'GOOG',
            'FB',
            'JNJ',
            'WMT',
            'V',
            'PG',
            'TDS',
            'DX',
            'AES',
            'AMKR',
            'AGO',
            'CAH',
            'CVS'
            ]
 
excel_dir = 'stock_market_data_history.xlsx'
with pd.ExcelWriter(excel_dir, engine='xlsxwriter') as writer:
    print("Creating file: {}".format(excel_dir))
    for ticker in tickers:
        print("Grabbing history for ticker: {}".format(ticker))
        dataframe = yf.Ticker(ticker)
        dataframe = dataframe.history(period="5d")
        if ticker is not None:    
            dataframe.to_excel(writer, f'{ticker}')
        else:
            print("No value for ticker.")

writer.save()    

def UpdateSheet():
    client = AuthorizeApi()
    sh = client.open_by_key("1IH6T9Dd98e-BeZrTVuSRf3rmTi74vOGFYx75Nhz-pKM")
    file = 'stock_market_data_history.xlsx'
    print("Processing file: {}".format(file))
    xl = pd.ExcelFile(file)
    for item in tickers:
        print("Uploading Ticker: {}".format(item))
        try:
            worksheet = sh.add_worksheet(title=item, rows="100", cols="20")
        except:
            print("Worksheet already exists: {}".format(item))
        worksheet = worksheet = sh.worksheet(item)
        worksheet.clear()
        dataframe = xl.parse(item)
        dataframe['Date'] = dataframe['Date'].astype(str)
        worksheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
        print("Upload Complete for: {}".format(item))
        time.sleep(1)

time.sleep(5)
UpdateSheet()
